"""
POLARIS-EMS — Pyomo MILP Optimization Model
SIH26061: Polar Energy Management & Resilience System

Formulates the mixed-integer linear programming (MILP) dispatch and unit commitment model.
Guarantees:
- Exact physical power balance (conservation of energy, zero unphysical generation)
- Generator unit commitment (online, start, stop binaries and min/max operating ranges)
- Battery electrochemical limits, cold-derated capacity, and throughput wear penalties
- Monotonic fuel inventory depletion and effective resupply safety horizons
- Thermal habitability persistence based on lumped capacitance equations
- Flexible load shifting within allowed multi-hour time windows
- Dependable reserve margin maintenance
- Terminal state protection for storage, fuel, and habitability (Correction 1)
"""

import pyomo.environ as pyo
from backend.optimizer.adapter import OptimizerModelInputs


def build_optimizer_model(inputs: OptimizerModelInputs) -> pyo.ConcreteModel:
    """Constructs a fully constrained Pyomo ConcreteModel from adapter inputs."""
    m = pyo.ConcreteModel(name="PolarisEMS_Optimizer")
    T = inputs.horizon_hours
    G = inputs.generator_count

    # 1. Sets
    m.T = pyo.RangeSet(0, T - 1)
    m.G = pyo.RangeSet(1, G)

    # 2. Decision Variables
    # Generator variables
    m.u = pyo.Var(m.G, m.T, domain=pyo.Binary, doc="Generator online commitment")
    m.v = pyo.Var(m.G, m.T, domain=pyo.NonNegativeReals, bounds=(0, 1), doc="Generator startup indicator")
    m.w = pyo.Var(m.G, m.T, domain=pyo.NonNegativeReals, bounds=(0, 1), doc="Generator shutdown indicator")
    m.p_gen = pyo.Var(m.G, m.T, domain=pyo.NonNegativeReals, doc="Generator power output (kW)")

    # Battery variables (Continuous bounds prevent branching explosion; wear penalty + round-trip losses enforce complementarity)
    m.p_chg = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds=(0, inputs.battery_max_charge_kw), doc="Battery charging power (kW)")
    m.p_dis = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds=(0, inputs.battery_max_discharge_kw), doc="Battery discharging power (kW)")
    m.soc = pyo.Var(m.T, domain=pyo.NonNegativeReals, bounds=(inputs.battery_min_soc, inputs.battery_max_soc), doc="Battery SOC")

    # Renewable variables
    m.p_solar = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Solar power injected (kW)")
    m.p_curt_solar = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Solar power curtailed (kW)")
    m.p_wind = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Wind power injected (kW)")
    m.p_curt_wind = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Wind power curtailed (kW)")

    # Load & heating variables
    m.p_crit_served = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Critical load served (kW)")
    m.p_crit_unserved = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Critical load unserved (kW)")
    m.p_noncrit_served = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Non-critical load served (kW)")
    m.p_noncrit_unserved = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Non-critical load unserved (kW)")
    m.p_flex_served = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Flexible load served (kW)")
    m.p_heat = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Electrical heating served (kW)")

    # Thermal & habitability variables
    m.t_indoor = pyo.Var(m.T, domain=pyo.Reals, doc="Indoor temperature (deg C)")
    m.s_temp = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Thermal deficit slack below safe min (deg C)")

    # Fuel variables
    m.fuel = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Fuel remaining (Liters)")
    m.fuel_burn = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Fuel burned in step (Liters)")

    # Reserve variables
    m.r_dep = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Dependable reserve margin (kW)")
    m.s_res = pyo.Var(m.T, domain=pyo.NonNegativeReals, doc="Reserve margin deficit slack (kW)")

    # 3. Constraints

    # A. Electrical Power Balance: Sources == Sinks
    def power_balance_rule(model, t):
        sources = model.p_solar[t] + model.p_wind[t] + sum(model.p_gen[g, t] for g in model.G) + model.p_dis[t]
        sinks = model.p_crit_served[t] + model.p_noncrit_served[t] + model.p_flex_served[t] + model.p_heat[t] + model.p_chg[t]
        return sources == sinks
    m.power_balance = pyo.Constraint(m.T, rule=power_balance_rule)

    # B. Load Service Balance
    def crit_balance_rule(model, t):
        return model.p_crit_served[t] + model.p_crit_unserved[t] == inputs.p_crit_req[t]
    m.crit_balance = pyo.Constraint(m.T, rule=crit_balance_rule)

    def noncrit_balance_rule(model, t):
        return model.p_noncrit_served[t] + model.p_noncrit_unserved[t] == inputs.p_noncrit_req[t]
    m.noncrit_balance = pyo.Constraint(m.T, rule=noncrit_balance_rule)

    # C. Flexible Load Conservation (Shift windows across each 24h block)
    block_size = 24
    num_blocks = (T + block_size - 1) // block_size
    m.Blocks = pyo.RangeSet(0, num_blocks - 1)

    def flex_energy_rule(model, b):
        start = b * block_size
        end = min(T, (b + 1) * block_size)
        req_energy = sum(inputs.p_flex_req[t] for t in range(start, end))
        return sum(model.p_flex_served[t] for t in range(start, end)) == req_energy
    m.flex_energy_conservation = pyo.Constraint(m.Blocks, rule=flex_energy_rule)

    def flex_cap_rule(model, t):
        # Flexible load capped at 2.5x nominal to allow shifting without causing massive spikes
        cap = max(10.0, inputs.p_flex_req[t] * 2.5)
        return model.p_flex_served[t] <= cap
    m.flex_cap = pyo.Constraint(m.T, rule=flex_cap_rule)

    # D. Renewable Inflows & Curtailment
    def solar_inflow_rule(model, t):
        return model.p_solar[t] + model.p_curt_solar[t] == inputs.p_solar_avail[t]
    m.solar_inflow = pyo.Constraint(m.T, rule=solar_inflow_rule)

    def wind_inflow_rule(model, t):
        return model.p_wind[t] + model.p_curt_wind[t] == inputs.p_wind_avail[t]
    m.wind_inflow = pyo.Constraint(m.T, rule=wind_inflow_rule)

    # E. Battery Storage Dynamics & Bounds
    def battery_soc_rule(model, t):
        c_usable = max(1.0, inputs.battery_usable_capacity_kwh[t])
        eta_chg = inputs.battery_charge_efficiency
        eta_dis = inputs.battery_discharge_efficiency
        dt = 1.0
        delta_soc = (eta_chg * model.p_chg[t] - (1.0 / eta_dis) * model.p_dis[t]) * dt / c_usable
        if t == 0:
            return model.soc[0] == inputs.initial_battery_soc + delta_soc
        return model.soc[t] == model.soc[t - 1] + delta_soc
    m.battery_soc_dyn = pyo.Constraint(m.T, rule=battery_soc_rule)

    # F. Generator Operating Envelope, Commitment Logic & Symmetry Breaking
    def gen_min_load_rule(model, g, t):
        p_min = round(inputs.generator_rated_kw * inputs.generator_min_loading_pct, 2)
        return model.p_gen[g, t] >= p_min * model.u[g, t]
    m.gen_min_load = pyo.Constraint(m.G, m.T, rule=gen_min_load_rule)

    def gen_max_load_rule(model, g, t):
        return model.p_gen[g, t] <= inputs.generator_rated_kw * model.u[g, t]
    m.gen_max_load = pyo.Constraint(m.G, m.T, rule=gen_max_load_rule)

    def gen_avail_rule(model, g, t):
        # Enforce availability: if unavailable, unit cannot be online
        is_avail = 1 if inputs.generator_availability[g][t] else 0
        return model.u[g, t] <= is_avail
    m.gen_avail = pyo.Constraint(m.G, m.T, rule=gen_avail_rule)

    def gen_symmetry_rule(model, g, t):
        # Symmetry breaking across identical available units to collapse combinatorial B&B search
        if g < inputs.generator_count:
            if inputs.generator_availability[g][t] and inputs.generator_availability[g + 1][t]:
                return model.u[g, t] >= model.u[g + 1, t]
        return pyo.Constraint.Skip
    m.gen_symmetry = pyo.Constraint(m.G, m.T, rule=gen_symmetry_rule)

    def gen_startup_rule(model, g, t):
        # Startup and shutdown transition logic
        if t == 0:
            u_prev = 1 if inputs.initial_generator_online.get(g, False) else 0
        else:
            u_prev = model.u[g, t - 1]
        return model.v[g, t] - model.w[g, t] == model.u[g, t] - u_prev
    m.gen_startup_rel = pyo.Constraint(m.G, m.T, rule=gen_startup_rule)

    # G. Fuel Depletion & Resupply Horizons (Correction 4)
    def fuel_burn_rule(model, t):
        dt = 1.0
        return model.fuel_burn[t] == sum(
            (inputs.generator_fuel_curve_l_per_kwh * model.p_gen[g, t] +
             inputs.generator_idle_fuel_l_per_h * model.u[g, t]) * dt
            for g in model.G
        )
    m.fuel_burn_calc = pyo.Constraint(m.T, rule=fuel_burn_rule)

    def fuel_inventory_rule(model, t):
        inflow = inputs.resupply_inflow_liters[t]
        if t == 0:
            return model.fuel[0] == inputs.initial_fuel_liters - model.fuel_burn[0] + inflow
        return model.fuel[t] == model.fuel[t - 1] - model.fuel_burn[t] + inflow
    m.fuel_inventory = pyo.Constraint(m.T, rule=fuel_inventory_rule)

    # Pre-resupply safety constraints (Correction 4)
    m.PreResupplySteps = pyo.Set(initialize=inputs.pre_resupply_timesteps)
    def pre_resupply_safety_rule(model, t):
        return model.fuel[t] >= inputs.critical_fuel_reserve_liters
    m.pre_resupply_safety = pyo.Constraint(m.PreResupplySteps, rule=pre_resupply_safety_rule)

    # H. Thermal Dynamics & Habitability
    def thermal_dyn_rule(model, t):
        c_th = inputs.thermal_capacitance_kwh_per_k
        ua_eff = inputs.building_ua_kw_per_k * (1.0 + inputs.ventilation_loss_coeff)
        q_int = inputs.internal_heat_gain_kw
        dt = 1.0
        if t == 0:
            t_prev = inputs.initial_indoor_temp_c
        else:
            t_prev = model.t_indoor[t - 1]
        t_amb = inputs.ambient_temp_c[t]
        # dT = (P_heat + Q_int - UA*(T_in - T_amb)) * dt / C_th
        q_loss = ua_eff * (t_prev - t_amb)
        q_net = model.p_heat[t] + q_int - q_loss
        return model.t_indoor[t] == t_prev + (q_net * dt / c_th)
    m.thermal_dyn = pyo.Constraint(m.T, rule=thermal_dyn_rule)

    def thermal_safe_rule(model, t):
        return model.t_indoor[t] + model.s_temp[t] >= inputs.min_safe_indoor_temp_c
    m.thermal_safe = pyo.Constraint(m.T, rule=thermal_safe_rule)

    # I. Dependable Reserve Margin
    def reserve_margin_rule(model, t):
        # Generator headroom + usable battery deliverable
        # Usable battery power constrained by SOC > SOC_min
        headroom_gen = sum(inputs.generator_rated_kw * model.u[g, t] - model.p_gen[g, t] for g in model.G)
        # Deliverable battery power linear approximation
        bat_deliverable = inputs.battery_max_discharge_kw * (model.soc[t] - inputs.battery_min_soc) / max(0.01, 1.0 - inputs.battery_min_soc)
        return model.r_dep[t] <= headroom_gen + bat_deliverable
    m.reserve_margin_calc = pyo.Constraint(m.T, rule=reserve_margin_rule)

    def reserve_req_rule(model, t):
        req_res = inputs.reserve_margin_pct * inputs.p_load_req[t]
        return model.r_dep[t] + model.s_res[t] >= req_res
    m.reserve_req = pyo.Constraint(m.T, rule=reserve_req_rule)

    # J. Terminal State Protection (Correction 1)
    # 1. Terminal Battery SOC
    m.terminal_soc_protect = pyo.Constraint(
        expr=m.soc[T - 1] >= inputs.terminal_soc_target
    )
    # 2. Terminal Fuel Reserve
    m.terminal_fuel_protect = pyo.Constraint(
        expr=m.fuel[T - 1] >= inputs.terminal_required_fuel
    )
    # 3. Terminal Reserve Margin
    m.terminal_reserve_protect = pyo.Constraint(
        expr=m.r_dep[T - 1] >= inputs.reserve_margin_pct * inputs.p_load_req[T - 1]
    )
    # 4. Terminal Indoor Temperature
    m.terminal_temp_protect = pyo.Constraint(
        expr=m.t_indoor[T - 1] >= min(inputs.target_indoor_temp_c, inputs.min_safe_indoor_temp_c + 2.0)
    )

    # 4. Multi-Objective Function
    w = inputs.weights
    w_fuel = w.get("w_fuel", 1.0)
    w_crit = w.get("w_crit", 100000.0)
    w_noncrit = w.get("w_noncrit", 500.0)
    w_thermal = w.get("w_thermal", 10000.0)
    w_reserve = w.get("w_reserve", 50.0)
    w_start = w.get("w_start", 5.0)
    w_bat = w.get("w_bat_wear", 0.05)  # Correction 3: wear proxy
    w_curt = w.get("w_curt", 0.01)

    def objective_rule(model):
        obj = 0
        for t in model.T:
            obj += w_fuel * model.fuel_burn[t]
            obj += w_crit * model.p_crit_unserved[t]
            obj += w_noncrit * model.p_noncrit_unserved[t]
            obj += w_thermal * model.s_temp[t]
            obj += w_reserve * model.s_res[t]
            obj += w_bat * (model.p_chg[t] + model.p_dis[t])
            obj += w_curt * (model.p_curt_solar[t] + model.p_curt_wind[t])
            obj += w_start * sum(model.v[g, t] for g in model.G)
        return obj

    m.objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    return m

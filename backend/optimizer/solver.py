"""
POLARIS-EMS — HiGHS Solver Interface & Solution Extractor
SIH26061: Polar Energy Management & Resilience System

Manages HiGHS solver invocation, options configuration, termination status handling,
and extraction of mathematical model solutions into strongly-typed DecisionStep records.
"""

from typing import Tuple, List, Optional, Dict, Any
import time
import pyomo.environ as pyo

from backend.optimizer.schema import (
    SolverStatus,
    DecisionStep,
    GeneratorScheduleStep,
    OptimizationSummary
)
from backend.optimizer.adapter import OptimizerModelInputs


class OptimizerSolver:
    """Manages execution of Pyomo MILP models via HiGHS."""

    def __init__(self, solver_name: str = "appsi_highs", time_limit_sec: float = 120.0, mip_gap: float = 0.03):
        """Initialize solver with a robust time limit and standard MIP relative gap."""
        self.solver_name = solver_name
        self.time_limit_sec = time_limit_sec
        self.mip_gap = mip_gap
        self._solver = None
        self._init_solver()

    def _init_solver(self) -> None:
        """Initialize the HiGHS solver and configure performance parameters."""
        try:
            self._solver = pyo.SolverFactory(self.solver_name)
            if not self._solver.available():
                self._solver = pyo.SolverFactory("highs")
        except Exception:
            self._solver = pyo.SolverFactory("highs")

        # Configure solver options
        if hasattr(self._solver, "config"):
            self._solver.config.time_limit = self.time_limit_sec
            self._solver.config.mip_gap = self.mip_gap
            self._solver.config.load_solution = False
        if hasattr(self._solver, "options"):
            self._solver.options["time_limit"] = self.time_limit_sec
            self._solver.options["mip_rel_gap"] = self.mip_gap
        if hasattr(self._solver, "highs_options"):
            self._solver.highs_options["time_limit"] = self.time_limit_sec
            self._solver.highs_options["mip_rel_gap"] = self.mip_gap

    def solve(
        self,
        model: pyo.ConcreteModel,
        inputs: OptimizerModelInputs
    ) -> Tuple[SolverStatus, float, str, Optional[List[DecisionStep]], Optional[OptimizationSummary]]:
        """
        Solves the model and extracts decisions.
        Handles optimal, infeasible, and timeout conditions cleanly.
        """
        start_t = time.perf_counter()

        try:
            res = self._solver.solve(model, load_solutions=False)
            solve_time = time.perf_counter() - start_t
            term_cond = str(getattr(res.solver, "termination_condition", "")).lower()
        except Exception as e:
            solve_time = time.perf_counter() - start_t
            return SolverStatus.ERROR, solve_time, str(e), None, None

        # Map solver termination condition
        if "infeasible" in term_cond:
            return SolverStatus.INFEASIBLE, solve_time, term_cond, None, None
        elif "unbounded" in term_cond:
            return SolverStatus.UNBOUNDED, solve_time, term_cond, None, None
        elif "optimal" in term_cond:
            status = SolverStatus.OPTIMAL
        elif "feasible" in term_cond:
            status = SolverStatus.FEASIBLE
        elif "timelimit" in term_cond or "max" in term_cond or "aborted" in term_cond:
            status = SolverStatus.TIME_LIMIT
        else:
            status = SolverStatus.ERROR

        # Load solution values into model
        loaded = False
        if hasattr(self._solver, "load_vars"):
            try:
                self._solver.load_vars()
                loaded = True
            except Exception:
                pass

        if not loaded:
            try:
                model.solutions.load_from(res)
                loaded = True
            except Exception as e:
                if status == SolverStatus.TIME_LIMIT:
                    return SolverStatus.TIME_LIMIT, solve_time, term_cond, None, None
                return SolverStatus.ERROR, solve_time, f"Failed to load solution: {str(e)}", None, None

        decision_schedule, summary = self._extract_solution(model, inputs)

        # Capture detailed solver telemetry (incumbent, best bound, relative MIP gap, optimality tier)
        incumbent_obj = summary.objective_value
        best_bound = None
        rel_gap = None
        if hasattr(self._solver, "_solver_model") and self._solver._solver_model is not None:
            try:
                info = self._solver._solver_model.getInfo()
                if hasattr(info, "objective_function_value"):
                    incumbent_obj = round(float(info.objective_function_value), 3)
                if hasattr(info, "mip_dual_bound"):
                    best_bound = round(float(info.mip_dual_bound), 3)
                if hasattr(info, "mip_gap"):
                    rel_gap = round(float(info.mip_gap), 5)
            except Exception:
                pass

        if hasattr(res, "problem") and best_bound is None:
            lb = getattr(res.problem, "lower_bound", None)
            if lb is not None:
                best_bound = round(float(lb), 3)

        if status == SolverStatus.OPTIMAL:
            if rel_gap is not None and rel_gap <= 1e-4:
                opt_tier = "EXACT_OPTIMAL"
            else:
                opt_tier = "MIP_GAP_OPTIMAL"
        elif status == SolverStatus.FEASIBLE:
            opt_tier = "GAP_ACCEPTED"
        elif status == SolverStatus.INFEASIBLE:
            opt_tier = "INFEASIBLE"
        elif status == SolverStatus.TIME_LIMIT:
            opt_tier = "TIME_LIMIT"
        else:
            opt_tier = "ERROR"

        self.last_solver_info = {
            "incumbent_objective": incumbent_obj,
            "best_bound": best_bound,
            "relative_mip_gap": rel_gap,
            "optimality_tier": opt_tier,
            "solve_time_seconds": round(solve_time, 3),
            "termination_condition": term_cond,
            "status": status
        }

        return status, solve_time, term_cond, decision_schedule, summary

    def _extract_solution(
        self,
        model: pyo.ConcreteModel,
        inputs: OptimizerModelInputs
    ) -> Tuple[List[DecisionStep], OptimizationSummary]:
        T = inputs.horizon_hours
        G = inputs.generator_count

        steps: List[DecisionStep] = []
        total_fuel = 0.0
        total_renew_gen = 0.0
        total_curt = 0.0
        total_crit_unserved = 0.0
        total_noncrit_unserved = 0.0
        total_starts = 0
        total_runtime = 0.0
        total_throughput = 0.0

        min_soc = 100.0
        min_indoor = 999.0
        deg_hours_violation = 0.0
        min_margin_pct = 999.0

        for t in range(T):
            # 1. Per-generator schedule
            gen_schedules: List[GeneratorScheduleStep] = []
            diesel_kw = 0.0
            online_count = 0
            for g in range(1, G + 1):
                u_val = float(pyo.value(model.u[g, t]))
                is_on = (u_val > 0.5)
                is_start = (float(pyo.value(model.v[g, t])) > 0.5)
                is_stop = (float(pyo.value(model.w[g, t])) > 0.5)
                p_g = round(float(pyo.value(model.p_gen[g, t])), 2)

                if is_on:
                    online_count += 1
                    total_runtime += 1.0
                if is_start:
                    total_starts += 1

                diesel_kw += p_g
                p_min_val = round(inputs.generator_rated_kw * inputs.generator_min_loading_pct, 2)
                gen_schedules.append(GeneratorScheduleStep(
                    generator_id=g,
                    is_online=is_on,
                    is_started=is_start,
                    is_stopped=is_stop,
                    power_kw=p_g,
                    rated_kw=inputs.generator_rated_kw,
                    min_power_kw=p_min_val
                ))

            # 2. Battery variables
            p_chg = round(float(pyo.value(model.p_chg[t])), 2)
            p_dis = round(float(pyo.value(model.p_dis[t])), 2)
            soc_pct = round(float(pyo.value(model.soc[t])) * 100.0, 2)
            c_usable = inputs.battery_usable_capacity_kwh[t]
            bat_energy = round((soc_pct / 100.0) * c_usable, 2)

            min_soc = min(min_soc, soc_pct)
            total_throughput += (p_chg + p_dis)

            # 3. Renewables
            p_sol = round(float(pyo.value(model.p_solar[t])), 2)
            p_curt_sol = round(float(pyo.value(model.p_curt_solar[t])), 2)
            p_wnd = round(float(pyo.value(model.p_wind[t])), 2)
            p_curt_wnd = round(float(pyo.value(model.p_curt_wind[t])), 2)

            total_renew_gen += (p_sol + p_wnd)
            total_curt += (p_curt_sol + p_curt_wnd)

            # 4. Loads & Heating
            p_crit_s = round(float(pyo.value(model.p_crit_served[t])), 2)
            p_crit_u = round(float(pyo.value(model.p_crit_unserved[t])), 2)
            p_noncrit_s = round(float(pyo.value(model.p_noncrit_served[t])), 2)
            p_noncrit_u = round(float(pyo.value(model.p_noncrit_unserved[t])), 2)
            p_flx = round(float(pyo.value(model.p_flex_served[t])), 2)
            p_ht = round(float(pyo.value(model.p_heat[t])), 2)

            # Reconcile rounding jitter across float additions
            tot_src = diesel_kw + p_sol + p_wnd + p_dis
            tot_snk = p_crit_s + p_noncrit_s + p_flx + p_ht + p_chg
            rounding_resid = round(tot_src - tot_snk, 4)
            if abs(rounding_resid) <= 0.05:
                p_noncrit_s = round(p_noncrit_s + rounding_resid, 2)

            total_crit_unserved += p_crit_u
            total_noncrit_unserved += p_noncrit_u

            # 5. Thermal & Fuel
            t_in = round(float(pyo.value(model.t_indoor[t])), 2)
            f_burn = round(float(pyo.value(model.fuel_burn[t])), 2)
            f_rem = round(float(pyo.value(model.fuel[t])), 2)
            total_fuel += f_burn

            min_indoor = min(min_indoor, t_in)
            if t_in < inputs.min_safe_indoor_temp_c:
                deg_hours_violation += (inputs.min_safe_indoor_temp_c - t_in)

            # 6. Reserves
            r_dep = round(float(pyo.value(model.r_dep[t])), 2)
            p_tot_load = inputs.p_load_req[t]
            margin_pct = round((r_dep / max(0.01, p_tot_load)) * 100.0, 1)
            min_margin_pct = min(min_margin_pct, margin_pct)

            steps.append(DecisionStep(
                timestamp=inputs.timestamps[t],
                horizon_h=t + 1,
                diesel_total_kw=round(diesel_kw, 2),
                online_generator_count=online_count,
                generator_schedules=gen_schedules,
                battery_charge_kw=p_chg,
                battery_discharge_kw=p_dis,
                battery_soc_pct=soc_pct,
                battery_energy_kwh=bat_energy,
                solar_generation_kw=p_sol,
                solar_curtailed_kw=p_curt_sol,
                wind_generation_kw=p_wnd,
                wind_curtailed_kw=p_curt_wnd,
                load_served_kw=round(p_crit_s + p_noncrit_s + p_flx, 2),
                load_unserved_kw=round(p_crit_u + p_noncrit_u, 2),
                critical_served_kw=p_crit_s,
                critical_unserved_kw=p_crit_u,
                flexible_served_kw=p_flx,
                heating_power_kw=p_ht,
                indoor_temp_c=t_in,
                fuel_burned_liters=f_burn,
                fuel_remaining_liters=f_rem,
                dependable_reserve_kw=r_dep,
                reserve_margin_pct=margin_pct
            ))

        total_avail_renew = sum(inputs.p_solar_avail) + sum(inputs.p_wind_avail)
        util_pct = round((total_renew_gen / max(0.01, total_avail_renew)) * 100.0, 1)
        final_soc = steps[-1].battery_soc_pct if steps else 0.0
        final_fuel = steps[-1].fuel_remaining_liters if steps else 0.0
        crit_passed = (total_crit_unserved < 1e-3 and min_indoor >= inputs.min_safe_indoor_temp_c - 0.1)

        summary = OptimizationSummary(
            total_fuel_consumed_liters=round(total_fuel, 2),
            final_fuel_remaining_liters=round(final_fuel, 2),
            total_renewable_generation_kwh=round(total_renew_gen, 2),
            total_renewable_curtailment_kwh=round(total_curt, 2),
            renewable_utilization_pct=util_pct,
            battery_throughput_kwh=round(total_throughput, 2),  # Correction 3
            min_battery_soc_pct=round(min_soc, 2),
            final_battery_soc_pct=round(final_soc, 2),
            total_critical_unserved_kwh=round(total_crit_unserved, 2),
            total_noncritical_unserved_kwh=round(total_noncrit_unserved, 2),
            critical_survival_passed=crit_passed,
            total_generator_starts=total_starts,
            total_generator_runtime_hours=round(total_runtime, 1),
            min_indoor_temp_c=round(min_indoor, 2),
            thermal_violation_degree_hours=round(deg_hours_violation, 2),
            min_reserve_margin_pct=round(min_margin_pct, 1),
            objective_value=round(float(pyo.value(model.objective)), 2)
        )

        return steps, summary

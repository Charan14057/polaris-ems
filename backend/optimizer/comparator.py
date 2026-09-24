"""
POLARIS-EMS — Counterfactual Optimizer Comparator
SIH26061: Polar Energy Management & Resilience System

Compares the candidate OPTIMIZED_DISPATCH schedule against the counterfactual
BASELINE_SIMULATION_DISPATCH reference run.
Guarantees:
- Exact numerical differential accounting
- Strict adherence to battery throughput and cycling terminology (Correction 3)
- Factual reporting with zero fabricated performance claims
"""

from typing import Dict, Any, List
from dataclasses import dataclass, asdict

from backend.twin.twin_engine import TwinTrajectory
from backend.optimizer.schema import OptimizationSummary


@dataclass
class CounterfactualComparison:
    """Exact differential comparison between Baseline and Optimized dispatch."""
    baseline_fuel_consumed_liters: float
    optimized_fuel_consumed_liters: float
    fuel_savings_liters: float
    fuel_savings_pct: float

    baseline_renewable_utilization_pct: float
    optimized_renewable_utilization_pct: float
    renewable_curtailment_reduction_kwh: float

    baseline_battery_throughput_kwh: float       # Correction 3: throughput/wear proxy
    optimized_battery_throughput_kwh: float
    battery_cycling_reduction_pct: float

    baseline_critical_unserved_kwh: float
    optimized_critical_unserved_kwh: float
    critical_unserved_eliminated_kwh: float

    baseline_total_unserved_kwh: float
    optimized_total_unserved_kwh: float
    total_unserved_reduction_kwh: float

    baseline_generator_starts: int
    optimized_generator_starts: int
    generator_start_reduction: int

    baseline_generator_runtime_hours: float
    optimized_generator_runtime_hours: float
    generator_runtime_reduction_hours: float

    baseline_min_soc_pct: float
    optimized_min_soc_pct: float

    baseline_min_indoor_temp_c: float
    optimized_min_indoor_temp_c: float

    baseline_min_reserve_margin_pct: float
    optimized_min_reserve_margin_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OptimizerComparator:
    """Computes exact metrics comparing baseline and optimized simulation outcomes."""

    @staticmethod
    def compare(
        baseline_trajectory: TwinTrajectory,
        optimized_summary: OptimizationSummary
    ) -> CounterfactualComparison:
        """Computes comprehensive numerical deltas between baseline and optimized runs."""
        b_sum = baseline_trajectory.summary

        b_fuel = float(b_sum.get("total_fuel_burned_liters", 0.0))
        o_fuel = optimized_summary.total_fuel_consumed_liters
        fuel_diff = round(b_fuel - o_fuel, 2)
        fuel_sav_pct = round((fuel_diff / max(0.01, b_fuel)) * 100.0, 1)

        b_curt = float(b_sum.get("total_curtailed_kwh", 0.0))
        o_curt = optimized_summary.total_renewable_curtailment_kwh
        curt_diff = round(b_curt - o_curt, 2)

        # Baseline renewable utilization
        b_renew_gen = 0.0
        b_throughput = 0.0
        b_starts = 0
        b_runtime = 0.0
        b_min_soc = 100.0
        b_min_temp = 999.0
        b_min_margin = 999.0

        prev_online = False
        for s in baseline_trajectory.states:
            # Use correct attribute names for solar and wind generation
            b_renew_gen += (s.solar.solar_generation_kw + s.wind.wind_generation_kw)
            b_throughput += (s.battery.charge_power_kw + s.battery.discharge_power_kw)
            is_on = (s.diesel.generator_status == "ONLINE")
            if is_on:
                b_runtime += 1.0
                if not prev_online:
                    b_starts += 1
            prev_online = is_on

            b_min_soc = min(b_min_soc, s.battery.soc_pct * 100.0)
            b_min_temp = min(b_min_temp, s.thermal.indoor_temp_c)
            if s.resilience:
                margin = (s.resilience.dependable_reserve_kw / max(0.01, s.loads.total_load_kw)) * 100.0
                b_min_margin = min(b_min_margin, margin)

        b_total_avail = b_renew_gen + b_curt
        b_util_pct = round((b_renew_gen / max(0.01, b_total_avail)) * 100.0, 1)

        # Battery throughput comparison (Correction 3)
        o_throughput = optimized_summary.battery_throughput_kwh
        tp_diff = round(b_throughput - o_throughput, 2)
        tp_red_pct = round((tp_diff / max(0.01, b_throughput)) * 100.0, 1)

        b_crit_u = float(b_sum.get("total_critical_unserved_kwh", 0.0))
        o_crit_u = optimized_summary.total_critical_unserved_kwh
        crit_elim = round(b_crit_u - o_crit_u, 2)

        b_tot_u = float(b_sum.get("total_unserved_kwh", 0.0))
        o_tot_u = optimized_summary.total_noncritical_unserved_kwh + o_crit_u
        tot_elim = round(b_tot_u - o_tot_u, 2)

        o_starts = optimized_summary.total_generator_starts
        starts_red = b_starts - o_starts

        o_runtime = optimized_summary.total_generator_runtime_hours
        runtime_red = round(b_runtime - o_runtime, 1)

        return CounterfactualComparison(
            baseline_fuel_consumed_liters=round(b_fuel, 2),
            optimized_fuel_consumed_liters=round(o_fuel, 2),
            fuel_savings_liters=fuel_diff,
            fuel_savings_pct=fuel_sav_pct,
            baseline_renewable_utilization_pct=b_util_pct,
            optimized_renewable_utilization_pct=optimized_summary.renewable_utilization_pct,
            renewable_curtailment_reduction_kwh=curt_diff,
            baseline_battery_throughput_kwh=round(b_throughput, 2),
            optimized_battery_throughput_kwh=round(o_throughput, 2),
            battery_cycling_reduction_pct=tp_red_pct,
            baseline_critical_unserved_kwh=round(b_crit_u, 2),
            optimized_critical_unserved_kwh=round(o_crit_u, 2),
            critical_unserved_eliminated_kwh=crit_elim,
            baseline_total_unserved_kwh=round(b_tot_u, 2),
            optimized_total_unserved_kwh=round(o_tot_u, 2),
            total_unserved_reduction_kwh=tot_elim,
            baseline_generator_starts=b_starts,
            optimized_generator_starts=o_starts,
            generator_start_reduction=starts_red,
            baseline_generator_runtime_hours=round(b_runtime, 1),
            optimized_generator_runtime_hours=round(o_runtime, 1),
            generator_runtime_reduction_hours=runtime_red,
            baseline_min_soc_pct=round(b_min_soc, 2),
            optimized_min_soc_pct=optimized_summary.min_battery_soc_pct,
            baseline_min_indoor_temp_c=round(b_min_temp, 2),
            optimized_min_indoor_temp_c=optimized_summary.min_indoor_temp_c,
            baseline_min_reserve_margin_pct=round(b_min_margin, 1),
            optimized_min_reserve_margin_pct=optimized_summary.min_reserve_margin_pct
        )

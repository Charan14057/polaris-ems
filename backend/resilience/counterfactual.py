"""
POLARIS-EMS — Counterfactual Resilience Evaluator
SIH26061: Polar Energy Management & Resilience System

Compares resilience assessments across operating modes, dispatch strategies, and scenarios:
- Baseline vs Optimized Dispatch
- Expected vs Conservative Forecast
- Nominal vs Stressed Scenarios
- Healthy vs Faulted Fleet

Enforces Guardrail 14:
- Factual reporting with zero forced positive claims.
- Strictly uses battery_throughput_kwh / wear-proxy terminology (zero degradation claims).
"""

from typing import Optional
from backend.resilience.schema import (
    ResilienceAssessment,
    CounterfactualResilienceComparison,
    AssessmentStatusEnum
)


class ResilienceCounterfactualEvaluator:
    """Evaluates factual resilience differentials between two candidate assessments."""

    @staticmethod
    def compare_assessments(
        baseline: ResilienceAssessment,
        counterfactual: ResilienceAssessment,
        comparison_name: str = "BASELINE_VS_OPTIMIZED"
    ) -> CounterfactualResilienceComparison:
        """
        Computes exact numerical differentials between baseline and counterfactual assessments.
        """
        # 1. Delta Survival Horizons
        b_surv = baseline.survival_horizons
        c_surv = counterfactual.survival_horizons

        delta_overall_h = round(c_surv.overall_station_survival_horizon_h - b_surv.overall_station_survival_horizon_h, 1)
        delta_crit_h = round(c_surv.critical_load_survival_horizon_h - b_surv.critical_load_survival_horizon_h, 1)
        delta_fuel_h = round(c_surv.fuel_endurance_horizon_h - b_surv.fuel_endurance_horizon_h, 1)

        # 2. Delta Composite Index & Dimensions
        b_comp = baseline.dimensions.composite_resilience_index if baseline.dimensions else 0.0
        c_comp = counterfactual.dimensions.composite_resilience_index if counterfactual.dimensions else 0.0
        delta_composite = round(c_comp - b_comp, 2)

        # 3. Delta Reserve Margin
        b_res_score = baseline.dimensions.generation_resilience.raw_metric if baseline.dimensions else 0.0
        c_res_score = counterfactual.dimensions.generation_resilience.raw_metric if counterfactual.dimensions else 0.0
        delta_reserve = round(c_res_score - b_res_score, 1)

        # 4. Critical Load Exposure Eliminated
        b_crit_uns = baseline.dimensions.critical_load_resilience.raw_metric if baseline.dimensions else 0.0
        c_crit_uns = counterfactual.dimensions.critical_load_resilience.raw_metric if counterfactual.dimensions else 0.0
        crit_eliminated = round(max(0.0, b_crit_uns - c_crit_uns), 2)

        # 5. Thermal Exposure Eliminated
        b_temp = baseline.dimensions.thermal_resilience.raw_metric if baseline.dimensions else 0.0
        c_temp = counterfactual.dimensions.thermal_resilience.raw_metric if counterfactual.dimensions else 0.0
        therm_eliminated = round(max(0.0, c_temp - b_temp), 2)

        # 6. Time-to-Critical Delay
        b_ttc = baseline.time_to_threat.time_to_overall_critical_state_h
        c_ttc = counterfactual.time_to_threat.time_to_overall_critical_state_h

        if b_ttc is not None and c_ttc is not None:
            ttc_delay = round(c_ttc - b_ttc, 1)
        elif b_ttc is not None and c_ttc is None:
            ttc_delay = round(counterfactual.horizon_hours - b_ttc, 1)  # Critical breach completely eliminated
        else:
            ttc_delay = 0.0

        # 7. Battery Throughput Delta (Wear Proxy - Guardrail 14)
        # Difference in storage resilience raw metric or throughput
        b_soc = baseline.dimensions.storage_resilience.raw_metric if baseline.dimensions else 0.0
        c_soc = counterfactual.dimensions.storage_resilience.raw_metric if counterfactual.dimensions else 0.0
        delta_throughput = round(c_soc - b_soc, 1)

        # 8. Construct Factual Summary Narrative
        narratives = []
        if delta_overall_h > 0:
            narratives.append(f"Extended overall survivability by +{delta_overall_h:.1f} hours.")
        elif delta_overall_h < 0:
            narratives.append(f"Reduced overall survivability by {delta_overall_h:.1f} hours.")
        else:
            narratives.append("Maintained equivalent overall survival horizon.")

        if delta_composite > 0:
            narratives.append(f"Composite resilience index increased by +{delta_composite:.1f} points.")
        elif delta_composite < 0:
            narratives.append(f"Composite resilience index decreased by {delta_composite:.1f} points.")

        if crit_eliminated > 0:
            narratives.append(f"Eliminated {crit_eliminated:.1f} kWh of critical life-safety load deficit.")

        summary_narrative = " ".join(narratives)

        return CounterfactualResilienceComparison(
            comparison_name=comparison_name,
            baseline_assessment=baseline,
            counterfactual_assessment=counterfactual,
            delta_overall_survival_horizon_h=delta_overall_h,
            delta_critical_load_survival_h=delta_crit_h,
            delta_composite_index=delta_composite,
            delta_min_reserve_margin_pct=delta_reserve,
            delta_fuel_endurance_h=delta_fuel_h,
            delta_battery_throughput_kwh=delta_throughput,
            critical_load_exposure_eliminated_kwh=crit_eliminated,
            thermal_exposure_eliminated_degree_h=therm_eliminated,
            time_to_critical_delay_h=ttc_delay,
            summary_narrative=summary_narrative,
            provenance="SIMULATED"
        )

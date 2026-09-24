"""
POLARIS-EMS — 9-Dimension Resilience Scoring Engine
SIH26061: Polar Energy Management & Resilience System

Calculates the 9 observable resilience dimensions and explainable composite index:
1. Energy Adequacy
2. Critical-Load Resilience
3. Thermal Resilience
4. Generation Resilience
5. Storage Resilience
6. Fuel Resilience
7. Logistics Resilience
8. Renewable Resilience
9. Recovery Resilience

Enforces Guardrails 10 & 17:
- All dimensions expose raw metrics, normalization formulas, thresholds, and weights.
- Composite index is an engineering index in [0.0, 100.0].
- Recovery resilience is strictly based on observable restorative capacity.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from backend.twin.state import TwinState
from backend.data.station_profiles.loader import StationProfile
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.resilience.schema import DimensionScore, ResilienceDimensions


class ResilienceMetricsEngine:
    """Evaluates the 9 transparent resilience dimensions and composite engineering index."""

    def __init__(
        self,
        profile: StationProfile,
        safety_registry: SafetyThresholdRegistry,
        weights_path: Optional[Path] = None
    ):
        self.profile = profile
        self.safety_registry = safety_registry
        self.weights_path = weights_path or (Path(__file__).resolve().parent.parent.parent / "configs" / "resilience_weights.json")
        self.weights = self._load_weights()

    def _load_weights(self) -> Dict[str, float]:
        """Loads dimension weights from configs/resilience_weights.json."""
        default_weights = {
            "energy_adequacy": 0.15,
            "critical_load_resilience": 0.20,
            "thermal_resilience": 0.15,
            "generation_resilience": 0.10,
            "storage_resilience": 0.10,
            "fuel_resilience": 0.10,
            "logistics_resilience": 0.10,
            "renewable_resilience": 0.05,
            "recovery_resilience": 0.05
        }
        if self.weights_path.exists():
            try:
                with open(self.weights_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    raw_w = data.get("weights", {})
                    return {k: float(v.get("weight", default_weights.get(k, 0.1))) for k, v in raw_w.items()}
            except Exception:
                return default_weights
        return default_weights

    def evaluate_dimensions(self, states: List[TwinState]) -> ResilienceDimensions:
        """
        Computes all 9 dimension scores from the authoritative TwinTrajectory states.
        """
        sid = self.profile.station_id.upper()
        min_safe_temp = self.safety_registry.get_value(sid, "indoor_min_safe_temp_c", default=12.0)
        fuel_reserve_l = self.safety_registry.get_value(sid, "fuel_reserve_liters", default=25000.0)
        gen_rated = float(self.profile.electrical.diesel_generator_kw_rated)
        gen_count = int(self.profile.electrical.diesel_generator_count)
        total_gen_cap = gen_rated * gen_count
        soc_min = float(self.profile.electrical.battery_min_soc)
        soc_max = float(self.profile.electrical.battery_max_soc)

        # Aggregate trajectory statistics
        tot_req_load = 0.0
        tot_served_load = 0.0
        tot_req_crit = 0.0
        tot_served_crit = 0.0
        tot_unserved_crit = 0.0
        min_indoor_temp = 999.0
        min_soc = 1.0
        min_fuel = 9999999.0
        min_headroom = 999999.0
        max_load = 0.0
        tot_renew_avail = 0.0
        tot_curtailed = 0.0
        pre_resupply_min_fuel = 9999999.0
        resupply_seen = False
        uncommitted_gen_sum = 0.0

        for state in states:
            req_l = state.loads.total_load_kw
            srv_l = state.loads.served_load_kw
            crit_l = state.loads.critical_load_kw
            srv_c = state.loads.served_critical_kw
            uns_c = state.loads.unserved_critical_kw

            tot_req_load += req_l
            tot_served_load += srv_l
            tot_req_crit += crit_l
            tot_served_crit += srv_c
            tot_unserved_crit += uns_c

            max_load = max(max_load, req_l)
            min_indoor_temp = min(min_indoor_temp, state.thermal.indoor_temperature_c)
            min_soc = min(min_soc, state.battery.soc_pct)
            min_fuel = min(min_fuel, state.fuel.fuel_remaining_l)

            # Available generator headroom
            active_gen_pwr = state.diesel.generator_power_kw
            headroom = max(0.0, state.diesel.generator_max_power_kw - active_gen_pwr) if state.diesel.generator_status != "FAULT" else 0.0
            min_headroom = min(min_headroom, headroom)

            # Uncommitted generation capability (for recovery)
            uncommitted = max(0.0, total_gen_cap - active_gen_pwr) if state.diesel.generator_status != "FAULT" else 0.0
            uncommitted_gen_sum += uncommitted

            # Renewables
            r_avail = state.solar.solar_available_kw + state.wind.wind_available_kw
            r_curt = state.solar.solar_curtailed_kw + state.wind.wind_curtailed_kw
            tot_renew_avail += r_avail
            tot_curtailed += r_curt

            # Resupply tracking
            if hasattr(state, "resupply") and state.resupply and state.resupply.resupply_event_active:
                resupply_seen = True
                pre_resupply_min_fuel = min(pre_resupply_min_fuel, state.fuel.fuel_remaining_l)

        if not resupply_seen:
            pre_resupply_min_fuel = min_fuel

        # --- Dimension 1: Energy Adequacy ---
        raw_ea = tot_served_load / max(0.01, tot_req_load)
        score_ea = round(min(100.0, max(0.0, raw_ea * 100.0)), 2)
        dim_ea = DimensionScore(
            dimension_name="energy_adequacy",
            raw_metric=round(raw_ea, 4),
            normalized_score=score_ea,
            weight=self.weights["energy_adequacy"],
            weighted_contribution=round(score_ea * self.weights["energy_adequacy"], 2),
            reference_threshold="1.0 (100% total electrical demand satisfied)",
            normalization_logic="100.0 * (served_kwh / requested_kwh)"
        )

        # --- Dimension 2: Critical Load Resilience ---
        raw_clr = tot_unserved_crit
        if tot_unserved_crit <= 1e-4:
            score_clr = 100.0
        else:
            fraction_served = tot_served_crit / max(0.01, tot_req_crit)
            score_clr = round(max(0.0, fraction_served * 100.0), 2)
        dim_clr = DimensionScore(
            dimension_name="critical_load_resilience",
            raw_metric=round(raw_clr, 2),
            normalized_score=score_clr,
            weight=self.weights["critical_load_resilience"],
            weighted_contribution=round(score_clr * self.weights["critical_load_resilience"], 2),
            reference_threshold="0.0 unserved critical kWh (Zero Tolerance)",
            normalization_logic="100.0 if unserved_crit == 0 else 100 * (served_crit / req_crit)"
        )

        # --- Dimension 3: Thermal Resilience ---
        thermal_margin = min_indoor_temp - min_safe_temp
        if min_indoor_temp < min_safe_temp:
            score_tr = round(max(0.0, 50.0 * (min_indoor_temp / max(1.0, min_safe_temp))), 2)
        else:
            score_tr = round(min(100.0, 70.0 + 3.0 * min(10.0, thermal_margin)), 2)
        dim_tr = DimensionScore(
            dimension_name="thermal_resilience",
            raw_metric=round(min_indoor_temp, 2),
            normalized_score=score_tr,
            weight=self.weights["thermal_resilience"],
            weighted_contribution=round(score_tr * self.weights["thermal_resilience"], 2),
            reference_threshold=f"{min_safe_temp:.1f} °C safe habitability limit",
            normalization_logic="70 + 3 * min(10, temp - safe_temp) if temp >= safe_temp else 50 * (temp / safe_temp)"
        )

        # --- Dimension 4: Generation Resilience (N-1 Redundancy) ---
        n_minus_1_cap = gen_rated * max(1, gen_count - 1)
        n_1_margin = n_minus_1_cap - max_load
        fault_present = any(s.diesel.generator_status == "FAULT" for s in states)
        if fault_present:
            score_gr = 40.0
        elif n_1_margin >= 0:
            score_gr = round(min(100.0, 75.0 + 25.0 * (n_1_margin / max(1.0, n_minus_1_cap))), 2)
        else:
            score_gr = round(max(20.0, 75.0 + 55.0 * (n_1_margin / max(1.0, max_load))), 2)
        dim_gr = DimensionScore(
            dimension_name="generation_resilience",
            raw_metric=round(n_1_margin, 2),
            normalized_score=score_gr,
            weight=self.weights["generation_resilience"],
            weighted_contribution=round(score_gr * self.weights["generation_resilience"], 2),
            reference_threshold=f"N-1 Generation Capacity ({n_minus_1_cap:.1f} kW) >= Peak Load ({max_load:.1f} kW)",
            normalization_logic="N-1 capacity headroom relative to station peak load"
        )

        # --- Dimension 5: Storage Resilience ---
        if min_soc <= soc_min:
            score_sr = 0.0
        else:
            usable_ratio = (min_soc - soc_min) / max(0.01, soc_max - soc_min)
            score_sr = round(min(100.0, max(0.0, usable_ratio * 100.0)), 2)
        dim_sr = DimensionScore(
            dimension_name="storage_resilience",
            raw_metric=round(min_soc * 100.0, 1),
            normalized_score=score_sr,
            weight=self.weights["storage_resilience"],
            weighted_contribution=round(score_sr * self.weights["storage_resilience"], 2),
            reference_threshold=f"SOC_min = {soc_min * 100:.0f}%, SOC_warning = 25%",
            normalization_logic="100.0 * (min_soc - soc_min) / (soc_max - soc_min)"
        )

        # --- Dimension 6: Fuel Resilience ---
        if min_fuel <= fuel_reserve_l:
            score_fr = round(max(0.0, 50.0 * (min_fuel / max(1.0, fuel_reserve_l))), 2)
        else:
            excess = min_fuel - fuel_reserve_l
            score_fr = round(min(100.0, 50.0 + 50.0 * min(1.0, excess / max(1.0, fuel_reserve_l))), 2)
        dim_fr = DimensionScore(
            dimension_name="fuel_resilience",
            raw_metric=round(min_fuel, 1),
            normalized_score=score_fr,
            weight=self.weights["fuel_resilience"],
            weighted_contribution=round(score_fr * self.weights["fuel_resilience"], 2),
            reference_threshold=f"{fuel_reserve_l:.0f} L emergency reserve",
            normalization_logic="Two-tier piecewise scaling above/below critical fuel reserve"
        )

        # --- Dimension 7: Logistics Resilience ---
        raw_lr = pre_resupply_min_fuel / max(1.0, fuel_reserve_l)
        score_lr = round(min(100.0, max(0.0, raw_lr * 100.0)), 2)
        dim_lr = DimensionScore(
            dimension_name="logistics_resilience",
            raw_metric=round(pre_resupply_min_fuel, 1),
            normalized_score=score_lr,
            weight=self.weights["logistics_resilience"],
            weighted_contribution=round(score_lr * self.weights["logistics_resilience"], 2),
            reference_threshold=f"Pre-resupply inventory >= {fuel_reserve_l:.0f} L reserve",
            normalization_logic="100.0 * min(1.0, pre_resupply_fuel / fuel_reserve_liters)"
        )

        # --- Dimension 8: Renewable Resilience ---
        curt_ratio = tot_curtailed / max(0.01, tot_renew_avail) if tot_renew_avail > 0.01 else 0.0
        score_rr = round(min(100.0, max(20.0, 100.0 - (curt_ratio * 40.0))), 2)
        dim_rr = DimensionScore(
            dimension_name="renewable_resilience",
            raw_metric=round((1.0 - curt_ratio) * 100.0, 1),
            normalized_score=score_rr,
            weight=self.weights["renewable_resilience"],
            weighted_contribution=round(score_rr * self.weights["renewable_resilience"], 2),
            reference_threshold="100% renewable utilization with minimal curtailment and no blackout",
            normalization_logic="100 - (curtailment_rate * 40)"
        )

        # --- Dimension 9: Recovery Resilience ---
        # Guardrail 17: Evaluates observable restorative capability
        avg_uncommitted_kw = uncommitted_gen_sum / max(1, len(states))
        recov_ratio = avg_uncommitted_kw / max(1.0, max_load)
        score_rec = round(min(100.0, max(0.0, recov_ratio * 100.0)), 2)
        dim_rec = DimensionScore(
            dimension_name="recovery_resilience",
            raw_metric=round(avg_uncommitted_kw, 1),
            normalized_score=score_rec,
            weight=self.weights["recovery_resilience"],
            weighted_contribution=round(score_rec * self.weights["recovery_resilience"], 2),
            reference_threshold="Surplus uncommitted generation headroom >= peak load",
            normalization_logic="100.0 * (avg_uncommitted_headroom_kw / peak_load_kw)"
        )

        # Compute Composite Engineering Index
        composite_index = round(
            dim_ea.weighted_contribution +
            dim_clr.weighted_contribution +
            dim_tr.weighted_contribution +
            dim_gr.weighted_contribution +
            dim_sr.weighted_contribution +
            dim_fr.weighted_contribution +
            dim_lr.weighted_contribution +
            dim_rr.weighted_contribution +
            dim_rec.weighted_contribution,
            2
        )

        return ResilienceDimensions(
            energy_adequacy=dim_ea,
            critical_load_resilience=dim_clr,
            thermal_resilience=dim_tr,
            generation_resilience=dim_gr,
            storage_resilience=dim_sr,
            fuel_resilience=dim_fr,
            logistics_resilience=dim_lr,
            renewable_resilience=dim_rr,
            recovery_resilience=dim_rec,
            composite_resilience_index=composite_index,
            provenance="CONFIGURED"
        )

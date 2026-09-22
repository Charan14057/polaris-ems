"""
POLARIS-EMS — Scenario Comparator & Failure Signature Engine
SIH26061: Polar Energy Management & Resilience System

Compares baseline trajectories against scenario trajectories to compute:
1. Exact numerical deltas across fuel, load, reserves, temperatures, and SOC.
2. Deterministic failure signature selection (Correction #5):
   - Earliest simulation timestep (T+h).
   - Fixed severity hierarchy for simultaneous failures:
     CRITICAL_LOAD_LOSS > THERMAL_BREACH > FUEL_RESERVE_BREACH > BATTERY_DEPLETION >
     GENERATION_SHORTFALL > RESUPPLY_DELAY_DEFICIT > RENEWABLE_FAILURE > GENERATOR_FAILURE
   - Captures primary_failure_signature and all secondary_failure_signatures.
3. First constraint violation and first threat state transition.
"""

from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from backend.scenarios.schema import ScenarioImpactMetrics
from backend.twin.twin_engine import TwinTrajectory


class ScenarioComparator:
    """Evaluates consequence deltas and failure signatures between baseline and scenario runs."""

    # Fixed severity hierarchy for simultaneous failure events (Correction #5)
    SEVERITY_HIERARCHY = [
        "CRITICAL_LOAD_LOSS",
        "THERMAL_BREACH",
        "FUEL_RESERVE_BREACH",
        "BATTERY_DEPLETION",
        "GENERATION_SHORTFALL",
        "RESUPPLY_DELAY_DEFICIT",
        "RENEWABLE_FAILURE",
        "GENERATOR_FAILURE"
    ]

    @classmethod
    def compare(
        cls,
        baseline: TwinTrajectory,
        scenario: TwinTrajectory
    ) -> ScenarioImpactMetrics:
        """
        Computes exact numerical deltas and identifies deterministic failure signatures.
        """
        b_sum = baseline.summary
        s_sum = scenario.summary
        b_df = baseline.to_dataframe()
        s_df = scenario.to_dataframe()

        # 1. Exact Numerical Deltas
        delta_fuel = round(s_sum.get("total_fuel_burned_liters", 0.0) - b_sum.get("total_fuel_burned_liters", 0.0), 2)
        delta_unserved = round(s_sum.get("total_unserved_kwh", 0.0) - b_sum.get("total_unserved_kwh", 0.0), 2)
        delta_crit_unserved = round(s_sum.get("total_critical_unserved_kwh", 0.0) - b_sum.get("total_critical_unserved_kwh", 0.0), 2)
        
        b_min_soc = b_df["battery_soc_pct"].min() * 100.0 if not b_df.empty else 0.0
        s_min_soc = s_df["battery_soc_pct"].min() * 100.0 if not s_df.empty else 0.0
        delta_min_soc = round(s_min_soc - b_min_soc, 2)

        b_min_res = b_df["dependable_reserve_pct"].min() if not b_df.empty else 0.0
        s_min_res = s_df["dependable_reserve_pct"].min() if not s_df.empty else 0.0
        delta_reserve = round(s_min_res - b_min_res, 1)

        b_min_cont = b_df["continuity_horizon_hours"].min() if not b_df.empty else 0.0
        s_min_cont = s_df["continuity_horizon_hours"].min() if not s_df.empty else 0.0
        delta_cont = round(s_min_cont - b_min_cont, 1)

        b_min_temp = b_df["indoor_temp_c"].min() if not b_df.empty else 0.0
        s_min_temp = s_df["indoor_temp_c"].min() if not s_df.empty else 0.0
        delta_temp = round(s_min_temp - b_min_temp, 2)

        # Diesel runtime
        b_runtime = (b_df["diesel_power_kw"] > 0.01).sum() if not b_df.empty else 0
        s_runtime = (s_df["diesel_power_kw"] > 0.01).sum() if not s_df.empty else 0
        delta_runtime = round(float(s_runtime - b_runtime), 1)

        # Renewable utilization
        b_ren = (b_df["solar_generation_kw"] + b_df["wind_generation_kw"]).sum() if not b_df.empty else 0.0
        s_ren = (s_df["solar_generation_kw"] + s_df["wind_generation_kw"]).sum() if not s_df.empty else 0.0
        delta_ren = round(s_ren - b_ren, 2)

        # 2. Failure Signature Analysis & Deterministic Resolution
        first_fail_h, primary_sig, secondary_sigs = cls._evaluate_failure_signatures(scenario)

        # 3. First Constraint Violation
        first_violation_desc = cls._detect_first_constraint_violation(scenario)

        # 4. First Threat State Transition
        first_threat_desc = cls._detect_first_threat_transition(baseline, scenario)

        return ScenarioImpactMetrics(
            delta_fuel_burn_liters=delta_fuel,
            delta_unserved_energy_kwh=delta_unserved,
            delta_critical_unserved_energy_kwh=delta_crit_unserved,
            delta_min_battery_soc=delta_min_soc,
            delta_reserve_margin_pct=delta_reserve,
            delta_continuity_horizon_hours=delta_cont,
            delta_min_indoor_temperature_c=delta_temp,
            delta_diesel_runtime_hours=delta_runtime,
            delta_renewable_utilization_pct=delta_ren,
            scenario_failure_time_h=first_fail_h,
            first_constraint_violation=first_violation_desc,
            first_threat_transition=first_threat_desc,
            primary_failure_signature=primary_sig,
            secondary_failure_signatures=secondary_sigs
        )

    @classmethod
    def _evaluate_failure_signatures(
        cls,
        scenario: TwinTrajectory
    ) -> Tuple[Optional[int], str, List[str]]:
        """
        Determines primary and secondary failure signatures using temporal earliest
        occurrence and fixed severity hierarchy precedence (Correction #5).
        """
        # Map failure types to their earliest timestep of occurrence
        detected_failures: Dict[str, int] = {}

        for h_idx, state in enumerate(scenario.states):
            h = h_idx + 1

            # A. Critical load unserved
            if state.loads.unserved_critical_kw > 1e-4:
                detected_failures.setdefault("CRITICAL_LOAD_LOSS", h)

            # B. Thermal breach
            min_safe_temp = state.thermal.indoor_min_safe_temp_c
            if state.thermal.indoor_temperature_c < min_safe_temp:
                detected_failures.setdefault("THERMAL_BREACH", h)

            # C. Fuel reserve breach
            if state.fuel.fuel_remaining_l <= state.fuel.fuel_reserve_l:
                detected_failures.setdefault("FUEL_RESERVE_BREACH", h)

            # D. Battery depletion under deficit
            if state.battery.soc_pct <= (state.battery.soc_min + 1e-3) and state.loads.unserved_load_kw > 1e-4:
                detected_failures.setdefault("BATTERY_DEPLETION", h)

            # E. Generation shortfall (unserved non-critical load)
            if state.loads.unserved_load_kw > 1e-4 and state.loads.unserved_critical_kw <= 1e-4:
                detected_failures.setdefault("GENERATION_SHORTFALL", h)

            # F. Resupply delay deficit (continuity horizon under 24h due to fuel exhaustion)
            if state.resilience and state.resilience.continuity_horizon_hours <= 24.0 and state.fuel.fuel_remaining_l <= state.fuel.fuel_reserve_l:
                detected_failures.setdefault("RESUPPLY_DELAY_DEFICIT", h)

            # G. Renewable asset trip
            if state.solar.solar_status == "FAULT" or state.wind.wind_status == "FAULT":
                detected_failures.setdefault("RENEWABLE_FAILURE", h)

            # H. Generator fault
            if state.diesel.generator_status == "FAULT":
                detected_failures.setdefault("GENERATOR_FAILURE", h)

        if not detected_failures:
            return None, "NOMINAL", []

        # Find earliest timestep across all detected failures
        earliest_step = min(detected_failures.values())
        earliest_candidates = [sig for sig, step in detected_failures.items() if step == earliest_step]

        # Break ties using fixed severity hierarchy
        earliest_candidates.sort(key=lambda s: cls.SEVERITY_HIERARCHY.index(s) if s in cls.SEVERITY_HIERARCHY else 999)
        primary_signature = earliest_candidates[0]

        # Secondary signatures: all other detected failures across the simulation
        secondary_signatures = [sig for sig in detected_failures.keys() if sig != primary_signature]
        secondary_signatures.sort(key=lambda s: cls.SEVERITY_HIERARCHY.index(s) if s in cls.SEVERITY_HIERARCHY else 999)

        return earliest_step, primary_signature, secondary_signatures

    @classmethod
    def _detect_first_constraint_violation(cls, scenario: TwinTrajectory) -> Optional[str]:
        """Finds the earliest violated constraint."""
        for h_idx, state in enumerate(scenario.states):
            h = h_idx + 1
            for c in state.constraints:
                if c.status == "VIOLATED":
                    return f"{c.constraint_name} at T+{h}h (Value: {c.value} {c.unit}, Limit: {c.limit} {c.unit})"
        return None

    @classmethod
    def _detect_first_threat_transition(
        cls,
        baseline: TwinTrajectory,
        scenario: TwinTrajectory
    ) -> Optional[str]:
        """Detects the earliest timestep where threat state worsened relative to baseline."""
        for h_idx in range(min(len(baseline.states), len(scenario.states))):
            h = h_idx + 1
            b_ts = baseline.states[h_idx].resilience.threat_state if baseline.states[h_idx].resilience else "SAFE"
            s_ts = scenario.states[h_idx].resilience.threat_state if scenario.states[h_idx].resilience else "SAFE"
            if b_ts != s_ts and s_ts in ["AT_RISK", "THREATENED", "CRITICAL"]:
                return f"Threat transitioned from {b_ts} to {s_ts} at T+{h}h"
        return None

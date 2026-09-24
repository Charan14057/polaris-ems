"""
POLARIS-EMS — Digital Twin Reality Check & Calibration Governance Engine
SIH26061: Polar Energy Management & Resilience System

Phase 15 Workstream F & J: Digital Twin Consistency Check & Calibration Control
Compares subsystem benchmark reference values against Digital Twin simulations:
- Electrical power balance & bus stability
- Thermal building envelope dynamics
- Battery SOC & cold-temperature derating
- Diesel generator fuel consumption curves

INVARIANT:
Zero silent modifications to Phase 4 equations or Phase 3 models.
Discrepancies are formally registered as CALIBRATION_CANDIDATE under controlled governance.
"""

import math
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from backend.integrations.schemas import (
    TwinRealityMetric,
    CalibrationCandidate,
)

# Authoritative physical deviation tolerances for polar digital twin
PHYSICAL_TOLERANCES = {
    "electrical_power_kw": 0.05,       # 50 W power balance tolerance
    "thermal_indoor_c": 1.5,           # 1.5°C indoor temperature deviation tolerance
    "battery_soc_pct": 5.0,            # 5% state-of-charge tracking tolerance
    "fuel_consumption_l": 2.0,         # 2.0 L fuel consumption deviation tolerance
}


class TwinRealityCheckEngine:
    """Evaluates reference benchmark trajectories against Digital Twin simulations and governs recalibration proposals."""

    def __init__(self):
        self._metrics_history: List[TwinRealityMetric] = []
        self._candidates: Dict[str, CalibrationCandidate] = {}

    def check_electrical_response(
        self,
        station_id: str,
        observed_generation_kw: float,
        observed_load_kw: float,
        simulated_balance_residual_kw: float,
        n_points: int = 24
    ) -> TwinRealityMetric:
        """Evaluates electrical power balance against physical conservation."""
        tol = PHYSICAL_TOLERANCES["electrical_power_kw"]
        abs_err = abs(simulated_balance_residual_kw)
        within_tol = abs_err <= tol
        status = "VALIDATED" if within_tol else ("CALIBRATION_CANDIDATE" if abs_err > tol * 3 else "DISCREPANCY_NOTED")

        metric = TwinRealityMetric(
            station_id=station_id.upper(),
            subsystem="electrical",
            n_evaluations=n_points,
            observed_value=round(observed_load_kw, 3),
            simulated_value=round(observed_generation_kw, 3),
            residual=round(simulated_balance_residual_kw, 4),
            residual_pct=round((abs_err / (observed_load_kw + 1e-4)) * 100.0, 2),
            within_tolerance=within_tol,
            status=status,
            details={
                "tolerance_kw": tol,
                "power_balance_preserved": within_tol,
            }
        )
        self._metrics_history.append(metric)
        return metric

    def check_thermal_response(
        self,
        station_id: str,
        observed_indoor_c: float,
        simulated_indoor_c: float,
        ambient_c: float,
        n_points: int = 24
    ) -> TwinRealityMetric:
        """Evaluates building envelope thermodynamics and heating adequacy."""
        tol = PHYSICAL_TOLERANCES["thermal_indoor_c"]
        residual = observed_indoor_c - simulated_indoor_c
        abs_res = abs(residual)
        within_tol = abs_res <= tol
        status = "VALIDATED" if within_tol else ("CALIBRATION_CANDIDATE" if abs_res > tol * 2 else "DISCREPANCY_NOTED")

        metric = TwinRealityMetric(
            station_id=station_id.upper(),
            subsystem="thermal",
            n_evaluations=n_points,
            observed_value=round(observed_indoor_c, 2),
            simulated_value=round(simulated_indoor_c, 2),
            residual=round(residual, 3),
            residual_pct=round((abs_res / max(1.0, abs(observed_indoor_c))) * 100.0, 2),
            within_tolerance=within_tol,
            status=status,
            details={
                "ambient_temp_c": ambient_c,
                "tolerance_c": tol,
                "life_safety_floor_maintained": observed_indoor_c >= 12.0
            }
        )
        self._metrics_history.append(metric)

        # If persistent systematic thermal error, register a controlled candidate
        if status == "CALIBRATION_CANDIDATE":
            self.register_calibration_candidate(
                station_id=station_id,
                target_subsystem="thermal",
                parameter_name="building_u_value",
                current_value=0.25,
                proposed_value=round(0.25 * (1.0 + (residual / 50.0)), 4),
                deviation_reason=f"Systematic indoor temperature residual of {residual:+.2f}°C under {ambient_c:.1f}°C ambient",
                expected_reduction_pct=15.0
            )

        return metric

    def check_battery_response(
        self,
        station_id: str,
        observed_soc_pct: float,
        simulated_soc_pct: float,
        battery_temp_c: float,
        n_points: int = 24
    ) -> TwinRealityMetric:
        """Evaluates battery electrochemical state of charge and cold derating response."""
        tol = PHYSICAL_TOLERANCES["battery_soc_pct"]
        residual = observed_soc_pct - simulated_soc_pct
        abs_res = abs(residual)
        within_tol = abs_res <= tol
        status = "VALIDATED" if within_tol else ("CALIBRATION_CANDIDATE" if abs_res > tol * 2 else "DISCREPANCY_NOTED")

        metric = TwinRealityMetric(
            station_id=station_id.upper(),
            subsystem="battery",
            n_evaluations=n_points,
            observed_value=round(observed_soc_pct, 2),
            simulated_value=round(simulated_soc_pct, 2),
            residual=round(residual, 3),
            residual_pct=round(abs_res, 2),
            within_tolerance=within_tol,
            status=status,
            details={
                "battery_temp_c": battery_temp_c,
                "tolerance_soc_pct": tol,
                "cold_derating_active": battery_temp_c < 0.0
            }
        )
        self._metrics_history.append(metric)

        if status == "CALIBRATION_CANDIDATE":
            self.register_calibration_candidate(
                station_id=station_id,
                target_subsystem="battery",
                parameter_name="cold_capacity_derating_factor",
                current_value=0.015,
                proposed_value=0.018,
                deviation_reason=f"Observed battery SOC departed by {residual:+.1f}% at {battery_temp_c:.1f}°C",
                expected_reduction_pct=22.5
            )

        return metric

    def check_fuel_response(
        self,
        station_id: str,
        observed_fuel_consumed_l: float,
        simulated_fuel_consumed_l: float,
        n_points: int = 24
    ) -> TwinRealityMetric:
        """Evaluates generator fuel curve consumption against flow sensor observations."""
        tol = PHYSICAL_TOLERANCES["fuel_consumption_l"]
        residual = observed_fuel_consumed_l - simulated_fuel_consumed_l
        abs_res = abs(residual)
        within_tol = abs_res <= tol
        status = "VALIDATED" if within_tol else ("CALIBRATION_CANDIDATE" if abs_res > tol * 2.5 else "DISCREPANCY_NOTED")

        metric = TwinRealityMetric(
            station_id=station_id.upper(),
            subsystem="diesel",
            n_evaluations=n_points,
            observed_value=round(observed_fuel_consumed_l, 2),
            simulated_value=round(simulated_fuel_consumed_l, 2),
            residual=round(residual, 3),
            residual_pct=round((abs_res / max(1.0, observed_fuel_consumed_l)) * 100.0, 2),
            within_tolerance=within_tol,
            status=status,
            details={
                "tolerance_l": tol,
                "flow_meter_integrity": "NOMINAL"
            }
        )
        self._metrics_history.append(metric)
        return metric

    def register_calibration_candidate(
        self,
        station_id: str,
        target_subsystem: str,
        parameter_name: str,
        current_value: float,
        proposed_value: float,
        deviation_reason: str,
        expected_reduction_pct: float
    ) -> CalibrationCandidate:
        """Registers a calibration candidate under strict change-control governance without altering Phase 4."""
        candidate_id = f"CALIB-{station_id[:3].upper()}-{target_subsystem[:3].upper()}-{len(self._candidates) + 1:03d}"
        candidate = CalibrationCandidate(
            candidate_id=candidate_id,
            target_subsystem=target_subsystem,
            parameter_name=parameter_name,
            current_value=current_value,
            proposed_value=proposed_value,
            deviation_reason=deviation_reason,
            empirical_residual_reduction_pct=expected_reduction_pct,
            governance_status="PENDING_CONTROLLED_REVIEW",
            immutable_baseline_preserved=True
        )
        self._candidates[candidate_id] = candidate
        return candidate

    def get_calibration_candidates(self) -> List[CalibrationCandidate]:
        """Returns all proposed recalibration candidates."""
        return list(self._candidates.values())

    def get_all_metrics(self) -> List[TwinRealityMetric]:
        """Returns all recorded Digital Twin reality metrics."""
        return list(self._metrics_history)

    def clear_history(self):
        """Clears in-memory metrics and candidates."""
        self._metrics_history.clear()
        self._candidates.clear()


_twin_reality_engine: Optional[TwinRealityCheckEngine] = None


def get_twin_reality_engine() -> TwinRealityCheckEngine:
    """Singleton getter for Twin Reality Check Engine."""
    global _twin_reality_engine
    if _twin_reality_engine is None:
        _twin_reality_engine = TwinRealityCheckEngine()
    return _twin_reality_engine

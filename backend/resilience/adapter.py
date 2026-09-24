"""
POLARIS-EMS — Resilience Data Adapter & Trajectory Ingestion
SIH26061: Polar Energy Management & Resilience System

Validates incoming Digital Twin trajectories, OptimizationResults, and Scenario lineage.
Enforces Guardrail 7: Never confuses data failure (NO_DATA, INPUT_INVALID) with station failure.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math
from datetime import datetime

from backend.twin.state import TwinState
from backend.twin.twin_engine import TwinTrajectory, TwinEngine
from backend.twin.forecast_adapter import TwinInputStep
from backend.twin.power_balance import DispatchResult
from backend.optimizer.schema import OptimizationResult
from backend.resilience.schema import AssessmentStatusEnum


@dataclass
class TrajectoryValidationResult:
    """Outcome of trajectory validation and extraction."""
    is_valid: bool
    status: AssessmentStatusEnum
    errors: List[str]
    trajectory: Optional[TwinTrajectory] = None
    station_id: str = "UNKNOWN"
    horizon_hours: int = 0
    provenance: str = "SIMULATED"


class ResilienceDataAdapter:
    """Validates and extracts time-series data for resilience analysis."""

    @staticmethod
    def validate_trajectory(
        trajectory: Any,
        expected_station_id: Optional[str] = None
    ) -> TrajectoryValidationResult:
        """
        Validates trajectory integrity, chronological monotonicity, and state completeness.
        Does NOT alter or fabricate data.
        """
        errors = []

        if trajectory is None:
            return TrajectoryValidationResult(
                is_valid=False,
                status=AssessmentStatusEnum.NO_DATA,
                errors=["Input trajectory is None"],
                station_id=expected_station_id or "UNKNOWN"
            )

        if not hasattr(trajectory, "states") or not isinstance(trajectory.states, list):
            return TrajectoryValidationResult(
                is_valid=False,
                status=AssessmentStatusEnum.INPUT_INVALID,
                errors=["Input object does not contain a valid states list"],
                station_id=getattr(trajectory, "station_id", expected_station_id or "UNKNOWN")
            )

        states = trajectory.states
        if len(states) == 0:
            return TrajectoryValidationResult(
                is_valid=False,
                status=AssessmentStatusEnum.NO_DATA,
                errors=["Trajectory contains zero states"],
                station_id=getattr(trajectory, "station_id", expected_station_id or "UNKNOWN"),
                horizon_hours=0
            )

        station_id = getattr(trajectory, "station_id", states[0].station_id if states else "UNKNOWN")
        if expected_station_id and station_id.upper() != expected_station_id.upper():
            errors.append(f"Station ID mismatch: expected {expected_station_id}, got {station_id}")

        # Chronological and field completeness check
        prev_dt = None
        for idx, state in enumerate(states):
            if not isinstance(state, TwinState):
                errors.append(f"State at index {idx} is not an instance of TwinState")
                continue

            # Timestamp check
            if not state.timestamp or not isinstance(state.timestamp, str):
                errors.append(f"State at index {idx} has missing or invalid timestamp")
            else:
                try:
                    clean_ts = state.timestamp.replace("Z", "+00:00")
                    curr_dt = datetime.fromisoformat(clean_ts)
                    if prev_dt and curr_dt < prev_dt:
                        errors.append(
                            f"Non-monotonic timestamp at index {idx}: {state.timestamp} precedes {states[idx - 1].timestamp}"
                        )
                    prev_dt = curr_dt
                except Exception:
                    # If ISO parsing fails, check simple lexicographical string sorting
                    if prev_dt and state.timestamp < states[idx - 1].timestamp:
                        errors.append(f"Non-monotonic timestamp string at index {idx}: {state.timestamp}")

            # Critical subsystem completeness & numerical sanity
            if not hasattr(state, "loads") or state.loads is None:
                errors.append(f"State at index {idx} is missing load subsystem")
            else:
                if math.isnan(state.loads.total_load_kw) or math.isinf(state.loads.total_load_kw):
                    errors.append(f"State at index {idx} has invalid NaN/Inf in total_load_kw")

            if not hasattr(state, "thermal") or state.thermal is None:
                errors.append(f"State at index {idx} is missing thermal subsystem")
            else:
                if math.isnan(state.thermal.indoor_temperature_c) or math.isinf(state.thermal.indoor_temperature_c):
                    errors.append(f"State at index {idx} has invalid NaN/Inf in indoor_temperature_c")

            if not hasattr(state, "battery") or state.battery is None:
                errors.append(f"State at index {idx} is missing battery subsystem")
            else:
                if math.isnan(state.battery.soc_pct) or math.isinf(state.battery.soc_pct):
                    errors.append(f"State at index {idx} has invalid NaN/Inf in battery.soc_pct")

            if not hasattr(state, "fuel") or state.fuel is None:
                errors.append(f"State at index {idx} is missing fuel subsystem")
            else:
                if math.isnan(state.fuel.fuel_remaining_l) or math.isinf(state.fuel.fuel_remaining_l):
                    errors.append(f"State at index {idx} has invalid NaN/Inf in fuel_remaining_l")

        if errors:
            return TrajectoryValidationResult(
                is_valid=False,
                status=AssessmentStatusEnum.INPUT_INVALID,
                errors=errors,
                station_id=station_id,
                horizon_hours=len(states)
            )

        return TrajectoryValidationResult(
            is_valid=True,
            status=AssessmentStatusEnum.COMPLETED,
            errors=[],
            trajectory=trajectory,
            station_id=station_id,
            horizon_hours=len(states),
            provenance=states[0].provenance if states else "SIMULATED"
        )

    @staticmethod
    def replay_optimization_result_through_twin(
        optimization_result: OptimizationResult,
        initial_state: TwinState,
        trajectory_steps: List[TwinInputStep],
        twin: TwinEngine,
        dt_hours: float = 1.0
    ) -> TrajectoryValidationResult:
        """
        Reconstructs the authoritative physical TwinTrajectory from an OptimizationResult
        by replaying the scheduled decisions through the Phase 4 Digital Twin.
        Preserves Guardrail 2: Digital Twin remains the sole physical authority.
        """
        if optimization_result is None:
            return TrajectoryValidationResult(
                is_valid=False,
                status=AssessmentStatusEnum.NO_DATA,
                errors=["OptimizationResult is None"]
            )

        if not optimization_result.decision_schedule:
            return TrajectoryValidationResult(
                is_valid=False,
                status=AssessmentStatusEnum.NO_DATA,
                errors=["OptimizationResult contains empty decision schedule"],
                station_id=optimization_result.station_id
            )

        # Build DispatchResult objects for each step
        dispatch_list: List[DispatchResult] = []
        for dec in optimization_result.decision_schedule:
            tot_served_load = round(dec.load_served_kw + dec.heating_power_kw, 2)
            sources = dec.solar_generation_kw + dec.wind_generation_kw + dec.diesel_total_kw + dec.battery_discharge_kw
            sinks = tot_served_load + dec.battery_charge_kw
            bal_err = round(abs(sources - sinks), 4)

            dispatch = DispatchResult(
                solar_generation_kw=dec.solar_generation_kw,
                wind_generation_kw=dec.wind_generation_kw,
                battery_charge_kw=dec.battery_charge_kw,
                battery_discharge_kw=dec.battery_discharge_kw,
                diesel_power_kw=dec.diesel_total_kw,
                curtailment_kw=dec.solar_curtailed_kw + dec.wind_curtailed_kw,
                served_load_kw=tot_served_load,
                unserved_load_kw=dec.load_unserved_kw,
                served_critical_kw=dec.critical_served_kw,
                unserved_critical_kw=dec.critical_unserved_kw,
                balance_error_kw=bal_err,
                is_balanced=(bal_err < 1e-2),
                policy_name="OPTIMIZED_DISPATCH"
            )
            dispatch_list.append(dispatch)

        replayed_traj, twin_valid, twin_errors = twin.simulate_dispatch(
            initial_state=initial_state,
            trajectory_steps=trajectory_steps,
            dispatch_schedule=dispatch_list,
            dispatch_policy="OPTIMIZED_DISPATCH",
            dt_hours=dt_hours
        )

        validation = ResilienceDataAdapter.validate_trajectory(
            replayed_traj,
            expected_station_id=optimization_result.station_id
        )

        if not twin_valid:
            validation.errors.extend([f"[TWIN_PHYSICAL_DISCREPANCY] {e}" for e in twin_errors])

        return validation

"""
POLARIS-EMS — Twin Replay Validator
SIH26061: Polar Energy Management & Resilience System

Validates candidate optimizer dispatch schedules through the authoritative Phase 4 Digital Twin.
Architecture:
    Candidate DecisionSchedule
                 ↓
    GeneratorReplayAdapter (Validates availability, fault/maintenance, commitment)
                 ↓
    DispatchResult List synthesis
                 ↓
    Phase 4 Twin Replay (Simulates nonlinear thermodynamics, battery, and fuel burn)
                 ↓
    Constraint & Energy Balance Audit
                 ↓
    OPTIMIZER_SCHEDULE_VALID / OPTIMIZER_SCHEDULE_INVALID
"""

from typing import List, Tuple, Dict, Any, Optional

from backend.twin.twin_engine import TwinEngine, TwinTrajectory
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.twin.power_balance import DispatchResult
from backend.optimizer.schema import DecisionStep
from backend.optimizer.generator_adapter import GeneratorReplayAdapter


class TwinReplayValidator:
    """Executes the closed-loop physical validation of optimizer dispatch schedules."""

    def __init__(
        self,
        twin: TwinEngine,
        generator_adapter: GeneratorReplayAdapter
    ):
        self.twin = twin
        self.generator_adapter = generator_adapter

    def validate_and_replay(
        self,
        initial_state: TwinState,
        trajectory: List[TwinInputStep],
        decision_schedule: List[DecisionStep],
        dt_hours: float = 1.0
    ) -> Tuple[bool, List[str], Optional[TwinTrajectory]]:
        """
        Replays candidate decisions step-by-step through the Phase 4 Digital Twin.
        Returns:
            (is_valid, validation_messages, replayed_trajectory)
        """
        messages: List[str] = []

        # 1. Validate per-generator schedules and compute aggregate outputs
        agg_steps, gen_valid, gen_errors = self.generator_adapter.process_schedule(decision_schedule)
        if not gen_valid:
            for err in gen_errors:
                messages.append(f"[GENERATOR_VALIDATION_ERROR] {err}")

        # 2. Build DispatchResult objects for Twin replay
        dispatch_list: List[DispatchResult] = []
        for t, (dec, agg) in enumerate(zip(decision_schedule, agg_steps)):
            tot_served_load = round(dec.load_served_kw + dec.heating_power_kw, 2)
            sources = (dec.solar_generation_kw + dec.wind_generation_kw +
                       agg.aggregate_diesel_power_kw + dec.battery_discharge_kw)
            sinks = tot_served_load + dec.battery_charge_kw
            bal_err = round(abs(sources - sinks), 4)

            dispatch = DispatchResult(
                solar_generation_kw=dec.solar_generation_kw,
                wind_generation_kw=dec.wind_generation_kw,
                battery_charge_kw=dec.battery_charge_kw,
                battery_discharge_kw=dec.battery_discharge_kw,
                diesel_power_kw=agg.aggregate_diesel_power_kw,  # from validated generator adapter
                curtailment_kw=dec.solar_curtailed_kw + dec.wind_curtailed_kw,
                served_load_kw=tot_served_load,
                unserved_load_kw=dec.load_unserved_kw,
                served_critical_kw=dec.critical_served_kw,
                unserved_critical_kw=dec.critical_unserved_kw,
                balance_error_kw=bal_err,
                is_balanced=(bal_err < 1e-3),
                policy_name="OPTIMIZED_DISPATCH"
            )
            dispatch_list.append(dispatch)

        # 3. Simulate through Phase 4 Digital Twin
        traj, twin_valid, twin_errors = self.twin.simulate_dispatch(
            initial_state=initial_state,
            trajectory_steps=trajectory,
            dispatch_schedule=dispatch_list,
            dispatch_policy="OPTIMIZED_DISPATCH",
            dt_hours=dt_hours
        )

        if not twin_valid:
            for err in twin_errors:
                messages.append(f"[TWIN_PHYSICS_VIOLATION] {err}")

        is_overall_valid = gen_valid and twin_valid
        return is_overall_valid, messages, traj

"""
POLARIS-EMS — Rolling-Horizon Receding Execution Engine
SIH26061: Polar Energy Management & Resilience System

Implements a closed-loop rolling (receding) horizon optimization framework.
Concept:
    At step t:
        1. Formulate MILP over lookahead horizon [t, t + H]
        2. Solve for optimal dispatch trajectory
        3. Apply first decision step (t) to current station state
        4. Step physical Digital Twin to generate next observed state
        5. Roll horizon forward: t <- t + 1
        6. Repeat with refreshed telemetry and forecast
"""

from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

from backend.twin.twin_engine import TwinEngine, TwinTrajectory
from backend.twin.state import TwinState
from backend.twin.forecast_adapter import TwinInputStep
from backend.twin.power_balance import DispatchResult
from backend.optimizer.schema import DecisionStep, OptimizationMode


@dataclass
class RollingExecutionResult:
    """Outcome of a closed-loop rolling-horizon simulation."""
    applied_decisions: List[DecisionStep]
    trajectory: TwinTrajectory
    total_solves: int
    successful_solves: int
    fallback_solves: int


class RollingHorizonOptimizer:
    """Orchestrates closed-loop receding-horizon optimization runs."""

    def __init__(
        self,
        optimizer_engine: Any,  # OptimizerEngine
        horizon_hours: int = 24,
        step_hours: int = 1
    ):
        self.optimizer_engine = optimizer_engine
        self.horizon_hours = horizon_hours
        self.step_hours = step_hours

    def run_rolling(
        self,
        initial_state: TwinState,
        full_trajectory: List[TwinInputStep],
        mode: OptimizationMode = OptimizationMode.EXPECTED,
        max_simulation_steps: Optional[int] = None
    ) -> RollingExecutionResult:
        """
        Executes rolling horizon loop over full_trajectory.
        """
        total_len = len(full_trajectory)
        if max_simulation_steps:
            total_len = min(total_len, max_simulation_steps)

        current_state = initial_state
        applied_decisions: List[DecisionStep] = []
        executed_states: List[TwinState] = []
        executed_inputs: List[TwinInputStep] = []
        dispatches: List[DispatchResult] = []

        successful_solves = 0
        fallback_solves = 0

        for k in range(0, total_len, self.step_hours):
            # Window slice
            window = full_trajectory[k : min(len(full_trajectory), k + self.horizon_hours)]
            if len(window) < 2:
                break

            # Optimize over window
            res = self.optimizer_engine.optimize(
                initial_state=current_state,
                trajectory=window,
                mode=mode
            )

            if res.solver_status.value in ("OPTIMAL", "FEASIBLE") and res.is_valid:
                successful_solves += 1
            else:
                fallback_solves += 1

            # Extract first decision step
            first_dec = res.decision_schedule[0]
            applied_decisions.append(first_dec)

            sources = (first_dec.solar_generation_kw + first_dec.wind_generation_kw +
                       first_dec.diesel_total_kw + first_dec.battery_discharge_kw)
            sinks = first_dec.load_served_kw + first_dec.battery_charge_kw
            bal_err = round(abs(sources - sinks), 4)

            dispatch = DispatchResult(
                solar_generation_kw=first_dec.solar_generation_kw,
                wind_generation_kw=first_dec.wind_generation_kw,
                battery_charge_kw=first_dec.battery_charge_kw,
                battery_discharge_kw=first_dec.battery_discharge_kw,
                diesel_power_kw=first_dec.diesel_total_kw,
                curtailment_kw=first_dec.solar_curtailed_kw + first_dec.wind_curtailed_kw,
                served_load_kw=first_dec.load_served_kw,
                unserved_load_kw=first_dec.load_unserved_kw,
                served_critical_kw=first_dec.critical_served_kw,
                unserved_critical_kw=first_dec.critical_unserved_kw,
                balance_error_kw=bal_err,
                is_balanced=(bal_err < 1e-3),
                policy_name="ROLLING_OPTIMIZED_DISPATCH"
            )
            dispatches.append(dispatch)
            executed_inputs.append(window[0])

            # Advance Twin physical state
            next_state = self.optimizer_engine.twin.step_with_dispatch(
                current_state=current_state,
                input_step=window[0],
                dispatch=dispatch,
                dispatch_policy="ROLLING_OPTIMIZED_DISPATCH",
                dt_hours=float(self.step_hours)
            )
            executed_states.append(next_state)
            current_state = next_state

        traj = TwinTrajectory(
            station_id=self.optimizer_engine.station_id,
            mode=mode.value if isinstance(mode, OptimizationMode) else str(mode),
            states=executed_states,
            summary={"steps": len(executed_states), "rolling_simulation": True}
        )

        return RollingExecutionResult(
            applied_decisions=applied_decisions,
            trajectory=traj,
            total_solves=successful_solves + fallback_solves,
            successful_solves=successful_solves,
            fallback_solves=fallback_solves
        )

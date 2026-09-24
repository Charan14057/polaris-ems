"""
POLARIS-EMS — Explicit Stateful Hysteresis & Anti-Churn Controller
SIH26061: Polar Energy Management & Resilience System

Implements explicit, pure-function hysteresis and anti-churn controllers.
Enforces Guardrail 2 & 10:
- Zero hidden global singletons or in-memory leakage.
- Accepts and returns explicit HysteresisState dataclass.
- Guarantees: same current inputs + same previous state -> identical policy result.
"""

from typing import Dict, Optional, Tuple
from backend.policy.schema import HysteresisState


class HysteresisController:
    """
    Evaluates threshold boundaries with explicit activation/deactivation deadbands.
    Prevents policy jitter/churn caused by microscopic numerical variations.
    """

    @staticmethod
    def evaluate_deadband(
        parameter_key: str,
        current_value: float,
        activation_threshold: float,
        deactivation_threshold: float,
        is_less_than_trigger: bool = True,
        previous_state: Optional[HysteresisState] = None,
        current_timestamp: str = "T+0",
        min_consecutive_steps: int = 1
    ) -> Tuple[bool, HysteresisState]:
        """
        Determines whether a policy trigger condition is active under deadband rules.

        For parameters where LOWER is more dangerous (e.g. reserve %, SOC %, temperature):
        - is_less_than_trigger = True
        - Triggers active if current_value <= activation_threshold
        - Once active, stays active until current_value >= deactivation_threshold
        (where deactivation_threshold > activation_threshold)

        For parameters where HIGHER is more dangerous (e.g. load, wind speed):
        - is_less_than_trigger = False
        - Triggers active if current_value >= activation_threshold
        - Once active, stays active until current_value <= deactivation_threshold
        """
        # Deepcopy or initialize state
        active_states = dict(previous_state.active_policy_states) if previous_state else {}
        consecutive = dict(previous_state.consecutive_steps) if previous_state else {}
        last_switch = dict(previous_state.last_switch_timestep) if previous_state else {}
        deadbands = dict(previous_state.deadbands) if previous_state else {}

        was_active = active_states.get(parameter_key, "INACTIVE") == "ACTIVE"
        prev_consecutive = consecutive.get(parameter_key, 0)

        # Store configured deadband magnitude
        deadbands[parameter_key] = abs(deactivation_threshold - activation_threshold)

        if is_less_than_trigger:
            # Low values trigger (e.g. reserve < 15%, SOC < 25%)
            if not was_active:
                if current_value <= activation_threshold:
                    new_consecutive = prev_consecutive + 1
                    if new_consecutive >= min_consecutive_steps:
                        active_states[parameter_key] = "ACTIVE"
                        consecutive[parameter_key] = new_consecutive
                        last_switch[parameter_key] = current_timestamp
                        is_active = True
                    else:
                        consecutive[parameter_key] = new_consecutive
                        is_active = False
                else:
                    consecutive[parameter_key] = 0
                    is_active = False
            else:
                # Currently active: requires rising past deactivation threshold to turn off
                if current_value >= deactivation_threshold:
                    active_states[parameter_key] = "INACTIVE"
                    consecutive[parameter_key] = 0
                    last_switch[parameter_key] = current_timestamp
                    is_active = False
                else:
                    consecutive[parameter_key] = prev_consecutive + 1
                    is_active = True
        else:
            # High values trigger (e.g. ambient wind >= 25 m/s)
            if not was_active:
                if current_value >= activation_threshold:
                    new_consecutive = prev_consecutive + 1
                    if new_consecutive >= min_consecutive_steps:
                        active_states[parameter_key] = "ACTIVE"
                        consecutive[parameter_key] = new_consecutive
                        last_switch[parameter_key] = current_timestamp
                        is_active = True
                    else:
                        consecutive[parameter_key] = new_consecutive
                        is_active = False
                else:
                    consecutive[parameter_key] = 0
                    is_active = False
            else:
                # Currently active: requires dropping below deactivation threshold to turn off
                if current_value <= deactivation_threshold:
                    active_states[parameter_key] = "INACTIVE"
                    consecutive[parameter_key] = 0
                    last_switch[parameter_key] = current_timestamp
                    is_active = False
                else:
                    consecutive[parameter_key] = prev_consecutive + 1
                    is_active = True

        new_state = HysteresisState(
            active_policy_states=active_states,
            consecutive_steps=consecutive,
            last_switch_timestep=last_switch,
            deadbands=deadbands
        )
        return is_active, new_state

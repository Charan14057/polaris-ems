"""
POLARIS-EMS — Per-Generator Replay Adapter
SIH26061: Polar Energy Management & Resilience System

Maps detailed per-generator unit commitment decisions (u[g,t], v[g,t], w[g,t], P[g,t])
into validated aggregate diesel power outputs for the Phase 4 Digital Twin replay loop.
Guarantees:
- Generator identity and individual availability preservation
- Detection and validation of fault / maintenance state violations
- Minimum and maximum loading envelope compliance per individual unit
- Exact aggregation of diesel power and online count for the physical Twin
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from backend.optimizer.schema import DecisionStep, GeneratorScheduleStep
from backend.twin.power_balance import DispatchResult


@dataclass
class ValidatedAggregateStep:
    """Aggregated dispatch candidate with per-generator audit trail."""
    timestamp: str
    horizon_h: int
    aggregate_diesel_power_kw: float
    online_generator_count: int
    generator_status: str  # "ONLINE" | "STANDBY"
    is_valid: bool
    validation_errors: List[str]
    per_generator_audit: List[GeneratorScheduleStep]


class GeneratorReplayAdapter:
    """Validates per-generator schedules and synthesizes aggregate inputs for Phase 4 Twin."""

    def __init__(
        self,
        generator_count: int,
        rated_kw: float,
        min_loading_pct: float,
        generator_availability: Optional[Dict[int, List[bool]]] = None
    ):
        self.generator_count = generator_count
        self.rated_kw = rated_kw
        self.min_loading_pct = min_loading_pct
        self.min_power_kw = rated_kw * min_loading_pct
        self.generator_availability = generator_availability or {
            g: [True] * 500 for g in range(1, generator_count + 1)
        }

    def validate_and_aggregate_step(
        self,
        decision_step: DecisionStep,
        step_idx: int
    ) -> ValidatedAggregateStep:
        """
        Validates individual unit commitment rules for a single step and computes aggregate output.
        """
        errors: List[str] = []
        agg_power = 0.0
        online_count = 0

        gen_scheds = decision_step.generator_schedules
        if len(gen_scheds) != self.generator_count:
            errors.append(f"Expected {self.generator_count} generators, got {len(gen_scheds)}")

        for g_sched in gen_scheds:
            g_id = g_sched.generator_id
            
            # Check availability
            is_avail = True
            if g_id in self.generator_availability:
                avail_list = self.generator_availability[g_id]
                if step_idx < len(avail_list):
                    is_avail = avail_list[step_idx]

            if not is_avail and g_sched.is_online:
                errors.append(
                    f"Generator {g_id} is marked OFFLINE/FAULT/MAINTENANCE at step {step_idx} "
                    f"but was committed online."
                )

            if g_sched.is_online:
                online_count += 1
                agg_power += g_sched.power_kw
                # Check min and max loading
                if g_sched.power_kw < self.min_power_kw - 1e-2:
                    errors.append(
                        f"Generator {g_id} power {g_sched.power_kw:.2f} kW is below min loading "
                        f"{self.min_power_kw:.2f} kW."
                    )
                if g_sched.power_kw > self.rated_kw + 1e-2:
                    errors.append(
                        f"Generator {g_id} power {g_sched.power_kw:.2f} kW exceeds rated "
                        f"{self.rated_kw:.2f} kW."
                    )
            else:
                if g_sched.power_kw > 1e-2:
                    errors.append(
                        f"Generator {g_id} is offline but has non-zero power {g_sched.power_kw:.2f} kW."
                    )

        gen_status = "ONLINE" if online_count > 0 else "STANDBY"
        is_valid = (len(errors) == 0)

        return ValidatedAggregateStep(
            timestamp=decision_step.timestamp,
            horizon_h=decision_step.horizon_h,
            aggregate_diesel_power_kw=round(agg_power, 2),
            online_generator_count=online_count,
            generator_status=gen_status,
            is_valid=is_valid,
            validation_errors=errors,
            per_generator_audit=gen_scheds
        )

    def process_schedule(
        self,
        decision_schedule: List[DecisionStep]
    ) -> Tuple[List[ValidatedAggregateStep], bool, List[str]]:
        """
        Processes an entire multi-timestep decision schedule.
        Returns aggregated steps, overall validity flag, and all validation error messages.
        """
        agg_steps: List[ValidatedAggregateStep] = []
        all_errors: List[str] = []
        is_overall_valid = True

        for t, step in enumerate(decision_schedule):
            val_step = self.validate_and_aggregate_step(step, t)
            agg_steps.append(val_step)
            if not val_step.is_valid:
                is_overall_valid = False
                for err in val_step.validation_errors:
                    all_errors.append(f"T+{t+1} ({step.timestamp}): {err}")

        return agg_steps, is_overall_valid, all_errors

"""
POLARIS-EMS — Multi-Horizon Risk-Aware Energy Optimizer Package
SIH26061: Polar Energy Management & Resilience System

Provides production optimization interfaces for polar station dispatch:
- OptimizerEngine: Primary interface for operational & strategic MILP dispatch
- RollingHorizonOptimizer: Closed-loop receded-horizon orchestrator
- GeneratorReplayAdapter: Per-generator validation & aggregate Twin mapping
- TwinReplayValidator: Closed-loop physical validation via Digital Twin
- OptimizerComparator: Counterfactual baseline vs optimized delta analyzer
- OptimizationResult, DecisionStep, GeneratorScheduleStep, OptimizationSummary
"""

from backend.optimizer.schema import (
    OptimizationMode,
    SolverStatus,
    GeneratorScheduleStep,
    DecisionStep,
    EffectiveResupplyEvent,
    OptimizationSummary,
    OptimizationResult
)
from backend.optimizer.adapter import OptimizerDataAdapter, OptimizerModelInputs
from backend.optimizer.model import build_optimizer_model
from backend.optimizer.solver import OptimizerSolver
from backend.optimizer.generator_adapter import GeneratorReplayAdapter, ValidatedAggregateStep
from backend.optimizer.replay import TwinReplayValidator
from backend.optimizer.comparator import OptimizerComparator, CounterfactualComparison
from backend.optimizer.rolling import RollingHorizonOptimizer, RollingExecutionResult
from backend.optimizer.engine import OptimizerEngine

__all__ = [
    "OptimizationMode",
    "SolverStatus",
    "GeneratorScheduleStep",
    "DecisionStep",
    "EffectiveResupplyEvent",
    "OptimizationSummary",
    "OptimizationResult",
    "OptimizerDataAdapter",
    "OptimizerModelInputs",
    "build_optimizer_model",
    "OptimizerSolver",
    "GeneratorReplayAdapter",
    "ValidatedAggregateStep",
    "TwinReplayValidator",
    "OptimizerComparator",
    "CounterfactualComparison",
    "RollingHorizonOptimizer",
    "RollingExecutionResult",
    "OptimizerEngine"
]

"""
POLARIS-EMS — Decision Trace & Audit Package
SIH26061: Polar Energy Management & Resilience System
"""

from backend.trace.schema import (
    TraceLifecycleState,
    TraceStage,
    ValidationTier,
    ReasonCode,
    TraceEvent,
    TraceSummary,
    DecisionExplanation,
    DecisionDelta,
    TraceRecord,
    LOCKED_PROVENANCE_TIERS,
    validate_provenance_tier
)
from backend.trace.builder import TraceEventBuilder
from backend.trace.lineage import LineageGraphBuilder
from backend.trace.explainer import DeterministicExplainer
from backend.trace.comparison import TraceComparisonEngine
from backend.trace.repository import TraceRepository, get_trace_repository
from backend.trace.engine import TraceService, get_trace_service

__all__ = [
    "TraceLifecycleState",
    "TraceStage",
    "ValidationTier",
    "ReasonCode",
    "TraceEvent",
    "TraceSummary",
    "DecisionExplanation",
    "DecisionDelta",
    "TraceRecord",
    "LOCKED_PROVENANCE_TIERS",
    "validate_provenance_tier",
    "TraceEventBuilder",
    "LineageGraphBuilder",
    "DeterministicExplainer",
    "TraceComparisonEngine",
    "TraceRepository",
    "get_trace_repository",
    "TraceService",
    "get_trace_service"
]

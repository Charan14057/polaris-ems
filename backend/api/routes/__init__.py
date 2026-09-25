"""
POLARIS-EMS — API Route Modules Package
SIH26061: Polar Energy Management & Resilience System
"""

from backend.api.routes.health import router as health_router
from backend.api.routes.stations import router as stations_router
from backend.api.routes.forecasts import router as forecasts_router
from backend.api.routes.scenarios import router as scenarios_router
from backend.api.routes.optimizer import router as optimizer_router
from backend.api.routes.resilience import router as resilience_router
from backend.api.routes.policy import router as policy_router
from backend.api.routes.pipeline import router as pipeline_router
from backend.api.routes.edge import router as edge_router
from backend.api.routes.traces import router as traces_router
from backend.api.routes.validation import router as validation_router
from backend.api.routes.integrations import router as integrations_router
from backend.api.routes.observability import router as observability_router
from backend.api.routes.twin import router as twin_router

__all__ = [
    "health_router",
    "stations_router",
    "forecasts_router",
    "scenarios_router",
    "optimizer_router",
    "resilience_router",
    "policy_router",
    "pipeline_router",
    "edge_router",
    "traces_router",
    "validation_router",
    "integrations_router",
    "observability_router",
    "twin_router",
]

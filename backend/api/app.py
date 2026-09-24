"""
POLARIS-EMS — FastAPI Application Factory
SIH26061: Polar Energy Management & Resilience System

Constructs and configures the production FastAPI application:
- Registers CORS and RequestCorrelationMiddleware.
- Configures structured exception handlers.
- Mounts versioned API routers under /api/v1 and health probes under /.
"""

from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.config import APIConfig, api_config
from backend.api.middleware import RequestCorrelationMiddleware
from backend.api.errors import (
    PolarisAPIException,
    polaris_exception_handler,
    validation_exception_handler,
    starlette_http_exception_handler,
    generic_exception_handler
)
from backend.api.routes import (
    health_router,
    stations_router,
    forecasts_router,
    scenarios_router,
    optimizer_router,
    resilience_router,
    policy_router,
    pipeline_router,
    edge_router
)


def create_app(config: Optional[APIConfig] = None) -> FastAPI:
    """Creates and configures a Polaris-EMS FastAPI application instance."""
    cfg = config or api_config

    app = FastAPI(
        title=cfg.title,
        description=cfg.description,
        version=cfg.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # 1. Register Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    app.add_middleware(RequestCorrelationMiddleware)

    # 2. Register Exception Handlers
    app.add_exception_handler(PolarisAPIException, polaris_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # 3. Mount Health Probes at Root Level
    app.include_router(health_router)

    # 4. Mount Versioned Business Endpoints under /api/v1
    v1_prefix = cfg.api_prefix
    app.include_router(health_router, prefix=v1_prefix)
    app.include_router(stations_router, prefix=v1_prefix)
    app.include_router(forecasts_router, prefix=v1_prefix)
    app.include_router(scenarios_router, prefix=v1_prefix)
    app.include_router(optimizer_router, prefix=v1_prefix)
    app.include_router(resilience_router, prefix=v1_prefix)
    app.include_router(policy_router, prefix=v1_prefix)
    app.include_router(pipeline_router, prefix=v1_prefix)
    app.include_router(edge_router, prefix=v1_prefix)

    @app.get("/", tags=["Root"])
    async def root():
        """Root API metadata and documentation link."""
        return {
            "name": cfg.title,
            "version": cfg.version,
            "api_version": "v1",
            "documentation": "/docs",
            "health": "/health",
            "endpoints_prefix": cfg.api_prefix
        }

    return app


# Default ASGI application instance
app = create_app()

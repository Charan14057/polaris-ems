"""
POLARIS-EMS — FastAPI Application Factory
SIH26061: Polar Energy Management & Resilience System

Constructs and configures the production FastAPI application:
- Registers CORS, RequestCorrelationMiddleware, SecurityHeadersMiddleware, and PayloadLimitMiddleware.
- Configures structured exception handlers.
- Mounts versioned API routers under /api/v1 and health probes under /.
- Optionally mounts pre-built React frontend static assets for single-port unified deployment.
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.config import APIConfig, api_config
from backend.api.middleware import (
    RequestCorrelationMiddleware,
    SecurityHeadersMiddleware,
    PayloadLimitMiddleware,
)
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
    edge_router,
    traces_router,
    validation_router,
    integrations_router,
    observability_router,
    twin_router
)

logger = logging.getLogger("polaris.app")


def create_app(config: Optional[APIConfig] = None) -> FastAPI:
    """Creates and configures a Polaris-EMS FastAPI application instance."""
    cfg = config or api_config

    @asynccontextmanager
    async def lifespan(app_instance: FastAPI):
        logger.info(
            f"Polaris-EMS API {cfg.version} initialized [Environment={cfg.settings.deployment.environment}, "
            f"Mode={cfg.settings.product.operator_mode}, SCADA_Connected={cfg.settings.product.physical_scada_connected}]"
        )
        yield
        logger.info("Polaris-EMS API shutting down gracefully.")

    app = FastAPI(
        title=cfg.title,
        description=cfg.description,
        version=cfg.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # 1. Register Middlewares (Order: Security Headers -> CORS -> Payload Limit -> Request Correlation)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    app.add_middleware(PayloadLimitMiddleware)
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
    app.include_router(traces_router, prefix=v1_prefix)
    app.include_router(validation_router, prefix=v1_prefix)
    app.include_router(integrations_router, prefix=v1_prefix)
    app.include_router(observability_router, prefix=v1_prefix)
    app.include_router(twin_router, prefix=v1_prefix)

    # 5. Optional Production Static Frontend Mounting
    if cfg.settings.deployment.serve_frontend and os.path.isdir(cfg.settings.deployment.frontend_dist_dir):
        logger.info(f"Mounting static frontend assets from {cfg.settings.deployment.frontend_dist_dir}")
        app.mount("/", StaticFiles(directory=cfg.settings.deployment.frontend_dist_dir, html=True), name="frontend")
    else:
        @app.get("/", tags=["Root"])
        async def root():
            """Root API metadata and documentation link."""
            return {
                "name": cfg.title,
                "version": cfg.version,
                "api_version": "v1",
                "documentation": "/docs",
                "health": "/health",
                "endpoints_prefix": cfg.api_prefix,
                "environment": cfg.settings.deployment.environment,
                "operator_mode": cfg.settings.product.operator_mode,
                "physical_scada_connected": cfg.settings.product.physical_scada_connected
            }

    return app


# Default ASGI application instance
app = create_app()

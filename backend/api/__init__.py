"""
POLARIS-EMS — API Integration Layer Package
SIH26061: Polar Energy Management & Resilience System

Provides production FastAPI backend exposing frozen Phase 1–8 capabilities:
- Station Configuration (Phase 1/2)
- ML Probabilistic Forecasting (Phase 3)
- Scenario Stress Testing (Phase 5)
- Energy Microgrid Optimization (Phase 6)
- Resilience Assessment (Phase 7)
- Policy Governance & Decision Trace (Phase 8)
- End-to-End Decision Pipeline
"""

from backend.api.config import APIConfig, api_config
from backend.api.app import create_app, app

__all__ = [
    "create_app",
    "app",
    "APIConfig",
    "api_config"
]

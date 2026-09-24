"""
POLARIS-EMS — API Configuration
SIH26061: Polar Energy Management & Resilience System

External configuration settings for FastAPI integration layer:
- Bridges to unified PolarisSettings hierarchy while maintaining backward compatibility.
"""

from typing import List, Optional
from dataclasses import dataclass, field
import os

from backend.config.settings import get_settings, PolarisSettings


@dataclass
class APIConfig:
    """Configurable environment parameters for Polaris-EMS API."""
    title: str = "Polaris-EMS API"
    description: str = "AI-Driven Smart Energy Management & Resilience System for Polar Research Stations"
    version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    host: str = field(default_factory=lambda: get_settings().app.host)
    port: int = field(default_factory=lambda: get_settings().app.port)
    cors_origins: List[str] = field(default_factory=lambda: get_settings().security.cors_origins)
    log_level: str = field(default_factory=lambda: get_settings().app.log_level)
    debug: bool = field(default_factory=lambda: get_settings().app.debug)
    settings: PolarisSettings = field(default_factory=get_settings)


# Global default configuration instance
api_config = APIConfig()

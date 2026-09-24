"""
POLARIS-EMS — API Configuration
SIH26061: Polar Energy Management & Resilience System

External configuration settings for FastAPI integration layer:
- Host, port, CORS origins, API version, log level, debug mode.
"""

from typing import List
from dataclasses import dataclass, field
import os


@dataclass
class APIConfig:
    """Configurable environment parameters for Polaris-EMS API."""
    title: str = "Polaris-EMS API"
    description: str = "AI-Driven Smart Energy Management & Resilience System for Polar Research Stations"
    version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    host: str = field(default_factory=lambda: os.getenv("POLARIS_API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("POLARIS_API_PORT", "8000")))
    cors_origins: List[str] = field(default_factory=lambda: [
        origin.strip()
        for origin in os.getenv("POLARIS_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    ])
    log_level: str = field(default_factory=lambda: os.getenv("POLARIS_LOG_LEVEL", "INFO"))
    debug: bool = field(default_factory=lambda: os.getenv("POLARIS_DEBUG", "false").lower() == "true")


# Global default configuration instance
api_config = APIConfig()

"""
POLARIS-EMS — Backend API Entrypoint Alias
Exposes `app` from `backend.api.app` for uvicorn standard CLI invocation.
"""

from backend.api.app import app, create_app

__all__ = ["app", "create_app"]

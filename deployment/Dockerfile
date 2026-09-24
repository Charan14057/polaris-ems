# ============================================================
# POLARIS-EMS — Production Multi-Stage Dockerfile
# SIH26061: Polar Energy Management & Resilience System
# ============================================================

# --- Stage 1: Build React Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci --silent || npm install --silent

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Runtime ---
FROM python:3.12-slim AS runtime

# Security: prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POLARIS_ENVIRONMENT=PRODUCTION \
    POLARIS_SERVE_FRONTEND=true \
    POLARIS_FRONTEND_DIST=/app/frontend/dist \
    POLARIS_API_HOST=0.0.0.0 \
    POLARIS_API_PORT=8000

WORKDIR /app

# Install minimal OS dependencies for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python production dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source code and configurations
COPY backend /app/backend
COPY configs /app/configs
COPY datasets /app/datasets
COPY models /app/models
COPY reports /app/reports

# Copy built frontend static assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Security: Create non-root polaris user
RUN useradd -u 10001 -m -s /bin/bash polarisuser && \
    mkdir -p /app/reports/traces && \
    chown -R polarisuser:polarisuser /app

USER polarisuser

# Healthcheck probe against FastAPI liveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Launch server with configurable workers
CMD ["python", "-m", "uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

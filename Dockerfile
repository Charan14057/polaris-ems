# ============================================================
# POLARIS-EMS — Production Multi-Stage Dockerfile
# Polar Energy Management & Resilience System
# ============================================================

# --- Stage 1: Build React Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install --silent

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Production Python Runtime ---
FROM python:3.12-slim AS runtime

# Security & runtime configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POLARIS_ENVIRONMENT=PRODUCTION \
    POLARIS_SERVE_FRONTEND=true \
    POLARIS_FRONTEND_DIST=/app/frontend/dist \
    POLARIS_API_HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

# Install minimal OS dependencies for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python production dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

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
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

EXPOSE 8000

# Launch server dynamically binding to Render's $PORT
CMD ["sh", "-c", "python -m uvicorn backend.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]

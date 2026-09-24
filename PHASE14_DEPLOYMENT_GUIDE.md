# POLARIS-EMS — PRODUCTION DEPLOYMENT GUIDE
**Enterprise Deployment, Containerization & Operational Runbook**

**System:** Polaris-EMS — Polar Energy Management & Resilience System  
**SIH Problem Statement:** SIH26061  
**Target Release:** Phase 14 (`PHASE_14_READY_TO_FREEZE`)  
**Deployment Profile:** Air-Gapped Polar Microgrid & Mission-Control Gateway

---

## 1. Architecture & Deployment Topology

Polaris-EMS is packaged as an enterprise mission-control application that can run in either **containerized orchestration** or **bare-metal single-port unified runtime**.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        POLARIS-EMS DEPLOYMENT                          │
├──────────────────────────────────────┬─────────────────────────────────┤
│         PRESENTATION LAYER           │       INTELLIGENCE BACKEND      │
│  React 18 + Vite (Tailwind/CSS)      │   FastAPI (Python 3.12 / 3.13)  │
│  Production Static Assets (dist/)     │   Uvicorn ASGI Gateway          │
│                                      │                                 │
│  - 10 Mission-Control Workspaces    │   - Conformal ML (P10..P95)     │
│  - Operator Review & Approval Banner │   - 4-Domain Digital Twin       │
│  - Explicit SCADA Disclaimer         │   - 14 Polar Stress Scenarios   │
│  - Immutable Trace Visualizer        │   - HiGHS MILP Microgrid Solver │
│                                      │   - 9-Dimension Resilience      │
│                                      │   - P1–P8 Policy Governance     │
│                                      │   - Immutable Decision Traces   │
└──────────────────────────────────────┴─────────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Disaggregated   │    │  External Reality│    │ Immutable Trace  │
│  Health Probes   │    │  Bridge Adapters │    │ Disk Storage     │
│  /health, /ready │    │  OpenMeteo, NCPOR│    │ ./reports/traces │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## 2. System Prerequisites

### Minimum Hardware Requirements:
- **CPU:** 2 Cores (4 Cores recommended for 168h strategic MILP solves).
- **RAM:** 4 GB (8 GB recommended when running high-dimensional Tree SHAP explanations).
- **Disk:** 5 GB free space for application runtime, model weights, and compressed decision trace storage.
- **Operating System:** Linux (Ubuntu 22.04 LTS / Debian 12 / Alpine), Windows 10/11, or macOS.

### Software Prerequisites:
- **Container Deployment:** Docker Engine 24.0+ and Docker Compose v2.20+.
- **Bare-Metal Deployment:**
  - Python 3.12 or 3.13 with `pip` and `virtualenv`.
  - Node.js 20 LTS and `npm` 10+ (for building frontend static bundle).
  - Pre-compiled `highs` binary solver (automatically provided via `highspy` Python wheel).

---

## 3. Environment Configuration & Secret Management

Copy the structured environment template to `.env`:

```bash
cp .env.example .env
```

### Core Configuration Parameters:

```ini
# ==============================================================================
# 1. APPLICATION RUNTIME & LOGGING
# ==============================================================================
POLARIS_HOST=0.0.0.0
POLARIS_PORT=8000
POLARIS_LOG_LEVEL=INFO
POLARIS_DEBUG=false
POLARIS_DOCS_ENABLED=true

# ==============================================================================
# 2. SECURITY & ACCESS CONTROL
# ==============================================================================
POLARIS_SECURITY_HEADERS=true
POLARIS_MAX_REQUEST_BYTES=10485760 # 10 MB payload limit
POLARIS_CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:8000"]

# ==============================================================================
# 3. EXTERNAL REALITY BRIDGE (WORKSTREAM C)
# ==============================================================================
POLARIS_EXTERNAL_DATA_ENABLED=false
POLARIS_EXTERNAL_TIMEOUT_SEC=10.0
POLARIS_EXTERNAL_MAX_FRESHNESS_SEC=3600
POLARIS_OPENMETEO_ENDPOINT=https://api.open-meteo.com/v1/forecast
# POLARIS_NCPOR_GATEWAY_URL=
# POLARIS_WEATHER_API_KEY=

# ==============================================================================
# 4. DEPLOYMENT & PERSISTENCE
# ==============================================================================
POLARIS_ENVIRONMENT=PRODUCTION
POLARIS_SERVE_FRONTEND=true
POLARIS_FRONTEND_DIST=frontend/dist
POLARIS_TRACE_DIR=reports/traces
POLARIS_TRACE_RETENTION_LIMIT=500

# ==============================================================================
# 5. PRODUCT & OPERATOR BOUNDARY
# ==============================================================================
POLARIS_PRODUCT_NAME=Polaris-EMS
POLARIS_OPERATOR_MODE=ADVISORY
POLARIS_PHYSICAL_SCADA_CONNECTED=false
```

> [!IMPORTANT]
> `POLARIS_PHYSICAL_SCADA_CONNECTED` must strictly remain `false`. Polaris-EMS currently operates in calibrated physics-based simulation mode. Zero connected physical polar SCADA telemetry exists.

---

## 4. Containerized Production Deployment

### Option A: Complete Multi-Stage Docker Build
Build the hardened, unprivileged container image:

```bash
docker build -t polaris-ems:1.0.0 -f deployment/Dockerfile .
```

Run container with resource constraints:

```bash
docker run -d \
  --name polaris-ems-prod \
  --restart unless-stopped \
  -p 8000:8000 \
  -v polaris_traces:/app/reports/traces \
  --env-file .env \
  polaris-ems:1.0.0
```

### Option B: Docker Compose Orchestration
Start the integrated production stack:

```bash
docker compose -f deployment/docker-compose.yml up -d
```

Check service status and container health:

```bash
docker compose -f deployment/docker-compose.yml ps
docker compose -f deployment/docker-compose.yml logs -f polaris-app
```

---

## 5. Bare-Metal Local / Air-Gapped Deployment

For air-gapped stations without container support:

### Step 1: Build Frontend Static Bundle
```bash
cd frontend
npm ci
npm run build
cd ..
```
*Output generated in `frontend/dist/`.*

### Step 2: Set Up Python Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Step 3: Launch Single-Port Unified Production Server
```bash
# Enable static frontend serving from FastAPI
export POLARIS_SERVE_FRONTEND=true
export POLARIS_ENVIRONMENT=PRODUCTION

uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

Access Mission Control in browser at: `http://localhost:8000`

---

## 6. Disaggregated Health Probes & Monitoring

Polaris-EMS disaggregates health reporting into 5 distinct operational endpoints:

| Endpoint | Probe Type | Purpose | Expected Status |
| :--- | :--- | :--- | :--- |
| `GET /health` | Liveness | Basic HTTP connectivity & process liveness | `200 OK` (`"service_status": "HEALTHY"`) |
| `GET /ready` or `/health/ready` | Readiness | Confirms loaded stations (3), scenarios (14), and models (9) | `200 OK` (`"ready": true`) |
| `GET /health/providers` | Data Feeds | Health and latency of external reality adapters | `200 OK` (`"healthy_providers": N`) |
| `GET /health/physical` | SCADA Truth | Physical hardware link disclosure (strictly disconnected) | `200 OK` (`"physical_scada_connected": false`) |
| `GET /health/engines` | Computation | Confirms online status of all 12 frozen computational engines | `200 OK` (All engines `"ONLINE"`) |
| `GET /api/v1/observability/metrics` | Observability | Runtime uptime, memory profile, median stage latencies | `200 OK` |
| `GET /api/v1/observability/audit` | Security Audit | Provenance compliance and epistemic authority verification | `200 OK` (`"status": "PASS"`) |

---

## 7. Operational Runbook & Troubleshooting

### Problem: Port 8000 or 3000 Conflict
- **Diagnosis:** `Address already in use`.
- **Resolution:** Check running processes (`netstat -ano | grep 8000` or `Get-NetTCPConnection -LocalPort 8000`). Stop orphan processes or configure alternate port via `POLARIS_PORT=8080`.

### Problem: Optimizer Returns Infeasible
- **Diagnosis:** Extreme scenario compound stress where load shedding is required.
- **Resolution:** The HiGHS optimizer gracefully falls back to priority-ordered emergency load shedding (P1 life-safety preserved, non-critical shed). Review stage diagnostics in `/api/v1/pipeline/analyze` response.

### Problem: External Weather Feed Unreachable / Stale
- **Diagnosis:** Satcom link failure in polar blizzard.
- **Resolution:** Polaris-EMS automatic fallback engages seamlessly. The reality bridge falls back to the physics-based synthetic environment without halting the dispatch pipeline. Degraded integration state is flagged in `/health/providers`.

---

## 8. Backup & Decision Trace Storage

- **Trace Repository:** All pipeline execution traces and deterministic explanations are persisted to `reports/traces/`.
- **Backup Command:**
  ```bash
  tar -czvf polaris_traces_backup_$(date +%Y%m%d).tar.gz reports/traces/
  ```
- **Retention Guard:** Governed by `POLARIS_TRACE_RETENTION_LIMIT=500`. Traces are preserved in chronological order.

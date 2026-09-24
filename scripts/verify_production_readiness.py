"""
POLARIS-EMS — Production Readiness Verification Script
Performs automated quality gate checks for productionization.

Usage: python scripts/verify_production_readiness.py
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results = []

def check(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    icon = PASS if passed else FAIL
    print(f"  {icon} {name}: {status}" + (f" — {detail}" if detail else ""))
    return passed


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ──────────────────────────────────────────────────────────────
# 1. SOURCE INTEGRITY
# ──────────────────────────────────────────────────────────────
section("1. SOURCE INTEGRITY")

# Check provenance taxonomy
provenance_file = ROOT / "frontend" / "src" / "api" / "types.ts"
if provenance_file.exists():
    content = provenance_file.read_text(encoding="utf-8")
    has_all_tiers = all(t in content for t in ["'REAL'", "'CONFIGURED'", "'ASSUMED'", "'SYNTHETIC'", "'FORECAST'", "'SIMULATED'"])
    check("Six-tier provenance taxonomy intact", has_all_tiers)
    # Check for prohibited tiers
    has_live = "'LIVE'" in content and "not.toContain" not in content
    has_realtime = "'REAL_TIME'" in content or "'REAL-TIME'" in content
    check("No prohibited LIVE provenance tier", not has_live)
    check("No prohibited REAL_TIME provenance tier", not has_realtime)
else:
    check("Provenance types file exists", False, "types.ts not found")


# ──────────────────────────────────────────────────────────────
# 2. SECRET SCAN
# ──────────────────────────────────────────────────────────────
section("2. SECRET SCAN")

secret_patterns = [r'api_key\s*=\s*["\'][^"\']+', r'password\s*=\s*["\'][^"\']+', r'secret\s*=\s*["\'][^"\']+']
secrets_found = []
for pattern in secret_patterns:
    for ext in ["*.py", "*.ts", "*.tsx", "*.json"]:
        for f in ROOT.rglob(ext):
            if ".venv" in str(f) or "node_modules" in str(f) or "__pycache__" in str(f):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    secrets_found.append(f"{f.relative_to(ROOT)}: {matches}")
            except Exception:
                pass

check("No hardcoded secrets in source", len(secrets_found) == 0,
      f"Found {len(secrets_found)} potential secrets" if secrets_found else "Clean")

# Check .env.example exists
check(".env.example exists", (ROOT / ".env.example").exists())

# Check no .env files committed
env_files = list(ROOT.glob(".env")) + list(ROOT.glob(".env.local")) + list(ROOT.glob(".env.production"))
check("No .env files in repository", len(env_files) == 0,
      f"Found: {[str(f.name) for f in env_files]}" if env_files else "Clean")


# ──────────────────────────────────────────────────────────────
# 3. ARCHITECTURAL BOUNDARIES
# ──────────────────────────────────────────────────────────────
section("3. ARCHITECTURAL BOUNDARIES")

# Check Pyomo only in optimizer/
pyomo_files = []
for f in (ROOT / "backend").rglob("*.py"):
    if "optimizer" in str(f).replace("\\", "/"):
        continue
    if "__pycache__" in str(f):
        continue
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
        if "import pyomo" in text or "from pyomo" in text:
            pyomo_files.append(str(f.relative_to(ROOT)))
    except Exception:
        pass
check("Pyomo restricted to Phase 6 optimizer", len(pyomo_files) == 0,
      f"Violations: {pyomo_files}" if pyomo_files else "Phase 6 only")

# Check HiGHS only in optimizer/
highs_files = []
for f in (ROOT / "backend").rglob("*.py"):
    if "optimizer" in str(f).replace("\\", "/"):
        continue
    if "__pycache__" in str(f):
        continue
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
        if "import highspy" in text or "from highspy" in text:
            highs_files.append(str(f.relative_to(ROOT)))
    except Exception:
        pass
check("HiGHS restricted to Phase 6 optimizer", len(highs_files) == 0,
      f"Violations: {highs_files}" if highs_files else "Phase 6 only")

# Check no physics in frontend
physics_terms = ["power_balance", "thermal_diff", "battery_degradation", "diesel_curve"]
frontend_physics = []
for f in (ROOT / "frontend" / "src").rglob("*.tsx"):
    if "test" in str(f).lower():
        continue
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for term in physics_terms:
            if term in text.lower():
                frontend_physics.append(f"{f.relative_to(ROOT)}: {term}")
    except Exception:
        pass
check("No physics equations in frontend", len(frontend_physics) == 0,
      f"Found: {frontend_physics}" if frontend_physics else "Clean")


# ──────────────────────────────────────────────────────────────
# 4. PRODUCTION BRANDING
# ──────────────────────────────────────────────────────────────
section("4. PRODUCTION BRANDING")

# Check for SIH in user-facing frontend (excluding test files and comments)
sih_in_ui = []
for f in (ROOT / "frontend" / "src").rglob("*.tsx"):
    if "test" in str(f).lower():
        continue
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
        # Only check non-comment lines for SIH in rendered JSX
        for i, line in enumerate(text.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                continue
            if "SIH" in line and "SIH" not in line.split("//")[-1] if "//" not in line else "SIH" in line.split("//")[0]:
                if ">" in line or "'" in line or '"' in line:
                    # Likely rendered text
                    sih_in_ui.append(f"{f.name}:{i}")
    except Exception:
        pass
check("No SIH in rendered frontend UI", len(sih_in_ui) == 0,
      f"Found: {sih_in_ui}" if sih_in_ui else "Clean")

# Check for REAL-TIME claims
realtime_claims = []
for f in (ROOT / "frontend" / "src").rglob("*.tsx"):
    if "test" in str(f).lower():
        continue
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.split("\n"), 1):
            if "REAL-TIME" in line or "REAL_TIME" in line:
                if "comment" not in line.lower() and not line.strip().startswith("//"):
                    realtime_claims.append(f"{f.name}:{i}")
    except Exception:
        pass
check("No false REAL-TIME claims in UI", len(realtime_claims) == 0,
      f"Found: {realtime_claims}" if realtime_claims else "Clean")


# ──────────────────────────────────────────────────────────────
# 5. CONFIGURATION CENTRALIZATION
# ──────────────────────────────────────────────────────────────
section("5. CONFIGURATION")

config_files = [
    "configs/station_profiles.json",
    "configs/device_profiles.json",
    "configs/policy_rules.json",
    "configs/resilience_weights.json",
    "configs/optimizer_weights.json",
    "configs/safety_thresholds.json",
]
for cf in config_files:
    check(f"Config exists: {cf}", (ROOT / cf).exists())


# ──────────────────────────────────────────────────────────────
# 6. HEALTH ENDPOINTS
# ──────────────────────────────────────────────────────────────
section("6. HEALTH ENDPOINTS")

health_routes = ROOT / "backend" / "api" / "routes" / "health.py"
if health_routes.exists():
    text = health_routes.read_text(encoding="utf-8")
    check("GET /health endpoint exists", "/health" in text)
    check("GET /health/ready endpoint exists", "/health/ready" in text)
    check("GET /health/capabilities endpoint exists", "/health/capabilities" in text)
else:
    check("Health routes file exists", False)


# ──────────────────────────────────────────────────────────────
# 7. ERROR HANDLING
# ──────────────────────────────────────────────────────────────
section("7. ERROR HANDLING")

errors_file = ROOT / "backend" / "api" / "errors.py"
if errors_file.exists():
    text = errors_file.read_text(encoding="utf-8")
    check("Structured error responses", "ErrorResponse" in text)
    check("No raw traceback leakage", "generic_exception_handler" in text)
    check("Request correlation in errors", "request_id" in text)
else:
    check("Error handlers exist", False)


# ──────────────────────────────────────────────────────────────
# 8. MIDDLEWARE
# ──────────────────────────────────────────────────────────────
section("8. MIDDLEWARE & OBSERVABILITY")

mw_file = ROOT / "backend" / "api" / "middleware.py"
if mw_file.exists():
    text = mw_file.read_text(encoding="utf-8")
    check("Request correlation middleware", "RequestCorrelationMiddleware" in text)
    check("Request timing headers", "X-Process-Time" in text)
    check("Request ID propagation", "X-Request-ID" in text)


# ──────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────
section("SUMMARY")

passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
total = len(results)

print(f"\n  Total checks: {total}")
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
print(f"  Pass rate: {passed/total*100:.1f}%")

if failed > 0:
    print(f"\n  {FAIL} PRODUCTION READINESS: NOT YET READY")
    print(f"  Failed checks:")
    for r in results:
        if r["status"] == "FAIL":
            print(f"    - {r['name']}: {r['detail']}")
    sys.exit(1)
else:
    print(f"\n  {PASS} PRODUCTION READINESS: ALL STATIC CHECKS PASSED")
    sys.exit(0)

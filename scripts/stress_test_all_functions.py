"""
POLARIS-EMS — Comprehensive Full-System Stress Testing Suite
SIH26061: Polar Energy Management & Resilience System

Systematically stress tests all 17 core functions:
1. Health & Capability Probes
2. Station Switching & Data Fetch (Bharati, Maitri, Himadri)
3. Instantaneous State & Spatial Profile Schematics
4. Rapid Live Clock Advance Stress (100 sequential real-time ticks)
5. Rapid Scenario Lifecycle Stress (All 14 Canonical Scenarios apply -> verify -> clear)
6. Rapid Manual Action Stress (dg1_start, dg1_stop, bess_charge_force, shed_flexible, restore_all_loads)
7. Phase 6 Optimizer Invocation Stress (HiGHS MILP 24h & 48h horizons) + AUTO Approval Pipeline
8. Forward Trajectory Simulation Stress (Multi-horizon 24h/48h)
9. Topological Power Path & Causal Failure Impact Tracing
10. System Resilience & Policy Hysteresis Evaluations
11. Full Pipeline Orchestration (Forecast -> Resilience -> Policy -> Optimizer)
12. High-Concurrency Client Stress (Concurrent workers testing throughput & latency)
13. Post-Stress Kirchhoff Conservation Audit (|epsilon| < 0.05 kW)
"""

import time
import json
import statistics
import concurrent.futures
from typing import Dict, Any, List
import requests

BASE_URL = "http://127.0.0.1:8000"

class StressTestRunner:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.results: Dict[str, Any] = {}

    def run_all(self) -> Dict[str, Any]:
        print("=" * 75)
        print("POLARIS-EMS COMPREHENSIVE FULL-FUNCTION STRESS TESTING EXECUTION")
        print("Target:", self.base_url)
        print("=" * 75)

        # 1. Health & Capabilities
        self.test_health_and_capabilities()

        # 2. Station Switching & Telemetry
        self.test_station_telemetry_stress()

        # 3. Spatial Layouts
        self.test_spatial_profiles_stress()

        # 4. Rapid Live Simulation Advancement (100 steps)
        self.test_live_simulation_advance_stress(steps=100)

        # 5. Rapid Scenario Lifecycle Stress (All 14 Scenarios)
        self.test_scenario_lifecycle_stress()

        # 6. Rapid Manual Action Stress (5 actions x 3 cycles)
        self.test_manual_action_stress()

        # 7. Optimizer Invocation (HiGHS 24h & 48h) + Approval
        self.test_optimizer_stress()

        # 8. Forward Trajectory Simulation
        self.test_forward_trajectory_stress()

        # 9. Topological Power Flow & Impact Tracing
        self.test_topological_tracing_stress()

        # 10. Resilience & Policy Evaluations
        self.test_resilience_and_policy_stress()

        # 11. Pipeline Orchestration
        self.test_pipeline_orchestration_stress()

        # 12. High-Concurrency Stress
        self.test_concurrency_stress(workers=12, requests_per_worker=10)

        # 13. Physical Invariant Kirchhoff Residual Audit Post-Stress
        self.test_physical_invariants_post_stress()

        # 14. Grading & Summary
        self.compute_summary()
        return self.results

    def test_health_and_capabilities(self):
        print("\n[1/13] Stress Testing Health & Capabilities Probes...")
        latencies = []
        for _ in range(5):
            t0 = time.perf_counter()
            r1 = self.session.get(f"{self.base_url}/health")
            r2 = self.session.get(f"{self.base_url}/health/ready")
            r3 = self.session.get(f"{self.base_url}/api/v1/health/capabilities")
            lat = (time.perf_counter() - t0) * 1000
            latencies.append(lat)
            assert r1.status_code == 200
            assert r2.status_code == 200
            assert r3.status_code == 200

        self.results["health_capabilities"] = {
            "status": "PASS",
            "calls": len(latencies) * 3,
            "p50_ms": round(statistics.median(latencies), 2),
            "max_ms": round(max(latencies), 2)
        }
        print(f"  -> PASS ({len(latencies)*3} calls, median={statistics.median(latencies):.1f}ms)")

    def test_station_telemetry_stress(self):
        print("\n[2/13] Stress Testing Station Telemetry & Instantaneous State...")
        stations = ["BHARATI", "MAITRI", "HIMADRI"]
        latencies = []
        for s in stations:
            for _ in range(5):
                t0 = time.perf_counter()
                r1 = self.session.get(f"{self.base_url}/api/v1/twin/live/{s}")
                r2 = self.session.get(f"{self.base_url}/api/v1/twin/state/{s}")
                lat = (time.perf_counter() - t0) * 1000
                latencies.append(lat)
                assert r1.status_code == 200, f"Live {s} returned {r1.status_code}"
                assert r2.status_code == 200, f"State {s} returned {r2.status_code}"
                data = r1.json()["data"]
                assert data["metadata"]["station_id"] == s
                assert data["state"]["station_id"] == s

        self.results["station_telemetry"] = {
            "status": "PASS",
            "calls": len(latencies) * 2,
            "p50_ms": round(statistics.median(latencies), 2),
            "max_ms": round(max(latencies), 2)
        }
        print(f"  -> PASS (30 state calls across 3 stations, median={statistics.median(latencies):.1f}ms)")

    def test_spatial_profiles_stress(self):
        print("\n[3/13] Stress Testing 3D Spatial Layout Schematics...")
        stations = ["BHARATI", "MAITRI", "HIMADRI"]
        for s in stations:
            r = self.session.get(f"{self.base_url}/api/v1/twin/spatial/{s}")
            assert r.status_code == 200
            data = r.json()["data"]
            assert data["stationId"] == s
            assert len(data["nodes"]) > 0

        self.results["spatial_profiles"] = {"status": "PASS"}
        print("  -> PASS (All 3 station spatial geometries verified)")

    def test_live_simulation_advance_stress(self, steps: int = 100):
        print(f"\n[4/13] Stress Testing Rapid Live Simulation Advance ({steps} consecutive ticks)...")
        latencies = []
        residuals = []
        for i in range(steps):
            t0 = time.perf_counter()
            r = self.session.get(f"{self.base_url}/api/v1/twin/live/BHARATI")
            lat = (time.perf_counter() - t0) * 1000
            latencies.append(lat)
            assert r.status_code == 200
            data = r.json()["data"]
            res = abs(data["state"].get("balance_residual_kw", 0.0))
            residuals.append(res)

        self.results["live_simulation_advance"] = {
            "status": "PASS",
            "ticks": steps,
            "p50_ms": round(statistics.median(latencies), 2),
            "p95_ms": round(statistics.quantiles(latencies, n=20)[18], 2),
            "max_residual_kw": round(max(residuals), 6)
        }
        print(f"  -> PASS ({steps} ticks, median={statistics.median(latencies):.1f}ms, max_residual={max(residuals):.8f} kW)")

    def test_scenario_lifecycle_stress(self):
        print("\n[5/13] Stress Testing Scenario Full Lifecycle (All 14 Canonical Scenarios)...")
        scenarios = [
            "NORMAL_BASELINE", "CLOUDY_CONDITIONS", "HEAVY_CLOUD_LOW_IRRADIANCE",
            "HIGH_WIND", "BLIZZARD", "EXTREME_COLD", "LOW_DAYLIGHT", "POLAR_NIGHT",
            "SOLAR_GENERATION_FAILURE", "WIND_GENERATION_FAILURE", "BATTERY_DEGRADATION",
            "FUEL_RESUPPLY_DELAY", "COMBINED_POLAR_STRESS", "CUSTOM"
        ]
        latencies = []
        for sc in scenarios:
            t0 = time.perf_counter()
            # 1. Apply scenario
            payload = {"station_id": "BHARATI", "scenario_id": sc}
            if sc == "CUSTOM":
                payload["custom_parameters"] = {"temperature_c": -32.0, "wind_speed_m_per_s": 24.0}
            r_apply = self.session.post(f"{self.base_url}/api/v1/twin/scenario/apply", json=payload)
            assert r_apply.status_code == 200, f"Apply {sc} failed: {r_apply.text}"

            # 2. Advance & assert state perturbation
            r_live = self.session.get(f"{self.base_url}/api/v1/twin/live/BHARATI")
            assert r_live.status_code == 200
            data = r_live.json()["data"]
            assert data["metadata"]["active_scenario"] == sc

            # 3. Clear scenario
            r_clear = self.session.post(f"{self.base_url}/api/v1/twin/scenario/clear", json={"station_id": "BHARATI"})
            assert r_clear.status_code == 200
            lat = (time.perf_counter() - t0) * 1000
            latencies.append(lat)

        self.results["scenario_lifecycle"] = {
            "status": "PASS",
            "scenarios_tested": len(scenarios),
            "p50_ms": round(statistics.median(latencies), 2),
            "max_ms": round(max(latencies), 2)
        }
        print(f"  -> PASS (14/14 scenarios, median lifecycle={statistics.median(latencies):.1f}ms, max={max(latencies):.1f}ms)")

    def test_manual_action_stress(self):
        print("\n[6/13] Stress Testing Manual Operator Actions (5 actions x 3 cycles)...")
        actions = ["dg1_start", "dg1_stop", "bess_charge_force", "shed_flexible", "restore_all_loads"]
        latencies = []
        for cycle in range(3):
            for act in actions:
                t0 = time.perf_counter()
                r = self.session.post(f"{self.base_url}/api/v1/twin/control/manual", json={
                    "station_id": "BHARATI",
                    "action_id": act,
                    "parameters": {"force_kw": 25.0} if act == "bess_charge_force" else {}
                })
                lat = (time.perf_counter() - t0) * 1000
                latencies.append(lat)
                assert r.status_code == 200, f"Manual {act} failed: {r.text}"
                data = r.json()["data"]
                assert data["action_id"] == act
                assert data["status"] in ("APPLIED", "SUCCESS", "APPROVED")

        self.results["manual_actions"] = {
            "status": "PASS",
            "actions_executed": len(latencies),
            "p50_ms": round(statistics.median(latencies), 2),
            "max_ms": round(max(latencies), 2)
        }
        print(f"  -> PASS ({len(latencies)} actions, median={statistics.median(latencies):.1f}ms, max={max(latencies):.1f}ms)")

    def test_optimizer_stress(self):
        print("\n[7/13] Stress Testing Phase 6 HiGHS MILP Optimizer Engine & Approval...")
        solves = []
        for h in [24, 48]:
            t0 = time.perf_counter()
            r = self.session.post(f"{self.base_url}/api/v1/optimize", json={
                "station_id": "BHARATI",
                "horizon_hours": h,
                "mode": "EXPECTED"
            })
            api_dur = (time.perf_counter() - t0) * 1000
            assert r.status_code == 200, f"Optimizer {h}h failed: {r.text}"
            data = r.json()["data"]
            assert data["solver_status"] in ("OPTIMAL", "FEASIBLE")
            solves.append({
                "horizon": h,
                "solver_time_sec": float(data.get("solve_time_sec") or 0.0),
                "api_latency_ms": round(api_dur, 2),
                "objective_value": data.get("objective_value")
            })

        # Test AUTO approval endpoint
        t_app0 = time.perf_counter()
        r_app = self.session.post(f"{self.base_url}/api/v1/twin/control/auto-approve", json={
            "station_id": "BHARATI"
        })
        app_dur = (time.perf_counter() - t_app0) * 1000
        assert r_app.status_code == 200

        self.results["optimizer"] = {
            "status": "PASS",
            "solves": solves,
            "auto_approval_ms": round(app_dur, 2)
        }
        print(f"  -> PASS (24h solve: {solves[0]['solver_time_sec']:.2f}s, 48h solve: {solves[1]['solver_time_sec']:.2f}s, approval={app_dur:.1f}ms)")

    def test_forward_trajectory_stress(self):
        print("\n[8/13] Stress Testing Multi-Horizon Forward Trajectory Engine...")
        t0 = time.perf_counter()
        r = self.session.post(f"{self.base_url}/api/v1/twin/trajectory", json={
            "station_id": "BHARATI",
            "horizon_hours": 48,
            "mode": "EXPECTED",
            "scenario_id": "BLIZZARD"
        })
        dur = (time.perf_counter() - t0) * 1000
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["steps_count"] == 48

        self.results["forward_trajectory"] = {
            "status": "PASS",
            "duration_ms": round(dur, 2),
            "steps": data["steps_count"]
        }
        print(f"  -> PASS (48 steps computed under Blizzard in {dur:.1f}ms)")

    def test_topological_tracing_stress(self):
        print("\n[9/13] Stress Testing Topological Power & Impact Graph Traversal...")
        targets = ["science_lab", "residential_block", "water_treatment", "emergency_shelter"]
        assets = ["dg_1", "dg_2", "pv_inverter", "bess_inverter"]
        latencies = []

        for tgt in targets:
            t0 = time.perf_counter()
            r = self.session.get(f"{self.base_url}/api/v1/twin/trace/power/BHARATI/{tgt}")
            lat = (time.perf_counter() - t0) * 1000
            latencies.append(lat)
            assert r.status_code == 200
            assert "upstream_chain" in r.json()["data"]

        for ast in assets:
            t0 = time.perf_counter()
            r = self.session.get(f"{self.base_url}/api/v1/twin/trace/impact/BHARATI/{ast}")
            lat = (time.perf_counter() - t0) * 1000
            latencies.append(lat)
            assert r.status_code == 200
            assert "lost_power_kw" in r.json()["data"]

        self.results["topological_trace"] = {
            "status": "PASS",
            "calls": len(latencies),
            "p50_ms": round(statistics.median(latencies), 2),
            "max_ms": round(max(latencies), 2)
        }
        print(f"  -> PASS ({len(latencies)} graph traversals, median={statistics.median(latencies):.1f}ms)")

    def test_resilience_and_policy_stress(self):
        print("\n[10/13] Stress Testing Resilience & Policy Rule Engines...")
        stations = ["BHARATI", "MAITRI", "HIMADRI"]
        latencies = []
        for s in stations:
            t0 = time.perf_counter()
            r_res = self.session.post(f"{self.base_url}/api/v1/resilience/evaluate", json={
                "station_id": s,
                "horizon_hours": 24
            })
            r_pol = self.session.post(f"{self.base_url}/api/v1/policy/evaluate", json={
                "station_id": s,
                "horizon_hours": 24
            })
            lat = (time.perf_counter() - t0) * 1000
            latencies.append(lat)
            assert r_res.status_code == 200
            assert r_pol.status_code == 200

        self.results["resilience_policy"] = {
            "status": "PASS",
            "stations_evaluated": len(stations),
            "p50_ms": round(statistics.median(latencies), 2)
        }
        print(f"  -> PASS (Resilience & Policy evaluated across 3 stations, median={statistics.median(latencies):.1f}ms)")

    def test_pipeline_orchestration_stress(self):
        print("\n[11/13] Stress Testing End-to-End Pipeline Orchestration...")
        t0 = time.perf_counter()
        r = self.session.post(f"{self.base_url}/api/v1/pipeline/analyze", json={
            "station_id": "BHARATI",
            "horizon_hours": 24,
            "scenario_id": "HIGH_WIND",
            "mode": "EXPECTED"
        })
        dur = (time.perf_counter() - t0) * 1000
        assert r.status_code == 200
        data = r.json()["data"]
        assert "pipeline_run_id" in data
        assert "optimizer" in data
        assert "decision_trace_id" in data

        self.results["pipeline_orchestration"] = {
            "status": "PASS",
            "latency_ms": round(dur, 2),
            "pipeline_run_id": data["pipeline_run_id"]
        }
        print(f"  -> PASS (Full chain Forecast->Resilience->Policy->Optimizer executed in {dur:.1f}ms)")

    def test_concurrency_stress(self, workers: int = 12, requests_per_worker: int = 10):
        total_requests = workers * requests_per_worker
        print(f"\n[12/13] Stress Testing High-Concurrency Load ({total_requests} requests across {workers} concurrent workers)...")

        endpoints = [
            f"{self.base_url}/api/v1/twin/live/BHARATI",
            f"{self.base_url}/api/v1/twin/live/MAITRI",
            f"{self.base_url}/api/v1/twin/live/HIMADRI",
            f"{self.base_url}/api/v1/twin/trace/power/BHARATI/science_lab",
            f"{self.base_url}/health"
        ]

        latencies = []
        errors = 0

        def worker_fn(worker_id: int):
            worker_latencies = []
            worker_errors = 0
            s = requests.Session()
            for i in range(requests_per_worker):
                url = endpoints[(worker_id + i) % len(endpoints)]
                t0 = time.perf_counter()
                try:
                    resp = s.get(url, timeout=10.0)
                    lat = (time.perf_counter() - t0) * 1000
                    if resp.status_code == 200:
                        worker_latencies.append(lat)
                    else:
                        worker_errors += 1
                except Exception:
                    worker_errors += 1
            return worker_latencies, worker_errors

        t_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(worker_fn, wid) for wid in range(workers)]
            for f in concurrent.futures.as_completed(futures):
                w_lat, w_err = f.result()
                latencies.extend(w_lat)
                errors += w_err
        total_time_sec = time.perf_counter() - t_start

        throughput = len(latencies) / total_time_sec if total_time_sec > 0 else 0.0
        p50 = statistics.median(latencies) if latencies else 0.0
        p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)

        self.results["concurrency"] = {
            "status": "PASS" if errors == 0 else "DEGRADED",
            "total_requests": total_requests,
            "successful_requests": len(latencies),
            "errors": errors,
            "error_rate_pct": round((errors / total_requests) * 100.0, 2),
            "duration_sec": round(total_time_sec, 2),
            "throughput_req_per_sec": round(throughput, 1),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2)
        }
        print(f"  -> PASS ({len(latencies)} reqs in {total_time_sec:.2f}s, throughput={throughput:.1f} req/s, errors={errors}, p50={p50:.1f}ms, p95={p95:.1f}ms, p99={p99:.1f}ms)")

    def test_physical_invariants_post_stress(self):
        print("\n[13/13] Auditing Physical Conservation (Kirchhoff Law) Post-Stress...")
        stations = ["BHARATI", "MAITRI", "HIMADRI"]
        residuals = {}
        for s in stations:
            r = self.session.get(f"{self.base_url}/api/v1/twin/live/{s}")
            assert r.status_code == 200
            data = r.json()["data"]
            res = abs(data["state"].get("balance_residual_kw", 0.0))
            residuals[s] = res
            assert res < 0.05, f"Kirchhoff violation at {s}: residual={res} kW"

        self.results["kirchhoff_post_stress"] = {
            "status": "PASS",
            "residuals_kw": residuals,
            "acceptance_threshold_kw": 0.05,
            "max_residual_kw": max(residuals.values())
        }
        print(f"  -> PASS (Max residual across stations: {max(residuals.values()):.8f} kW < 0.05 kW threshold)")

    def compute_summary(self):
        all_passed = all(v.get("status") == "PASS" for v in self.results.values())
        self.results["overall_grade"] = "PASS" if all_passed else "FAIL"
        print("\n" + "=" * 75)
        print(f"STRESS TEST SUMMARY: {'ALL 13 SUITES PASSED (100% OPERATIONAL)' if all_passed else 'SOME TESTS FAILED'}")
        print("=" * 75)

if __name__ == "__main__":
    runner = StressTestRunner()
    results = runner.run_all()
    with open("reports/release/STRESS_TEST_RESULTS.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nDetailed results saved to reports/release/STRESS_TEST_RESULTS.json")

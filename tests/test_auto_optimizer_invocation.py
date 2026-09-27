"""
POLARIS-EMS — Auto Optimizer Hard Proof Test Suite
Verifies that approve_auto_recommendation() actually invokes Phase 6 OptimizerEngine,
solves via HiGHS, returns validated optimization results, and applies authoritative dispatch.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.twin.live_session import LiveTwinSession
from backend.optimizer.schema import OptimizationMode, SolverStatus


def test_auto_optimizer_real_invocation_and_telemetry():
    """Verify that approve_auto_recommendation invokes OptimizerEngine.optimize and records HiGHS results."""
    session = LiveTwinSession("BHARATI")
    
    # Spy on real optimizer invocation
    real_optimize = session.optimizer_engine.optimize
    call_records = []

    def spy_optimize(*args, **kwargs):
        res = real_optimize(*args, **kwargs)
        call_records.append((args, kwargs, res))
        return res

    session.optimizer_engine.optimize = spy_optimize

    result = session.approve_auto_recommendation()

    # 1. Assert OptimizerEngine was genuinely invoked
    assert len(call_records) == 1, "OptimizerEngine.optimize must be invoked exactly once on approval"
    _, kwargs, opt_res = call_records[0]
    assert kwargs.get("mode") == OptimizationMode.EXPECTED
    assert len(kwargs.get("trajectory", [])) == 24, "Lookahead horizon must be 24 hours"

    # 2. Assert HiGHS solver output
    assert result["optimizer_class"] == "OptimizerEngine"
    assert result["solver"] == "HiGHS"
    assert result["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert result["horizon_hours"] == 24
    assert result["run_id"].startswith("opt-")
    assert result["objective_value"] > 0.0
    assert result["total_fuel_consumed_liters"] >= 0.0
    assert result["twin_replay_valid"] is True

    # 3. Assert Trace Event
    latest_trace = session.trace_history[-1]
    assert latest_trace["event"] == "AUTO_RECOMMENDATION_APPROVED"
    assert latest_trace["optimizer_run_id"] == result["run_id"]
    assert latest_trace["solver"] == "HiGHS"
    assert latest_trace["twin_replay_valid"] is True


def test_auto_optimizer_under_wind_failure_scenario():
    """Verify that applying WIND_GENERATION_FAILURE causes optimizer to schedule diesel compensation."""
    session = LiveTwinSession("BHARATI")
    session.apply_scenario("WIND_GENERATION_FAILURE")
    
    result = session.approve_auto_recommendation()

    assert result["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert result["twin_replay_valid"] is True
    # Under wind failure, diesel must be dispatched to preserve grid balance and spinning reserve
    state = result["state"]
    diesel_kw = state["diesel"]["generator_power_kw"]
    assert diesel_kw >= 24.0, f"Diesel generator must dispatch at or above minimum loading under wind failure, got {diesel_kw}"


def test_auto_optimizer_no_heuristic_replacement():
    """Verify that approve_auto_recommendation does not use a simplistic if-renewable-gt-load heuristic."""
    session = LiveTwinSession("BHARATI")
    
    # Mock optimizer to verify that approve_auto_recommendation strictly respects optimizer result
    mock_result = MagicMock()
    mock_result.solver_status = SolverStatus.OPTIMAL
    mock_result.solver_time_seconds = 0.042
    mock_result.run_id = "opt-mock-test-1234"
    mock_result.horizon_hours = 24
    mock_result.summary.objective_value = 123.45
    mock_result.summary.total_fuel_consumed_liters = 67.89
    mock_result.is_valid = True
    mock_result.validation_messages = ["MOCK_OPTIMIZER_VERIFIED"]
    
    # Mock decision schedule: explicitly dispatch diesel at 48.0 kW
    mock_decision = MagicMock()
    mock_decision.diesel_total_kw = 48.0
    mock_decision.battery_charge_kw = 10.0
    mock_decision.battery_discharge_kw = 0.0
    mock_result.decision_schedule = [mock_decision]

    with patch.object(session.optimizer_engine, "optimize", return_value=mock_result) as mock_opt:
        res = session.approve_auto_recommendation()
        assert mock_opt.called
        assert res["run_id"] == "opt-mock-test-1234"
        assert res["optimizer_class"] == "OptimizerEngine"
        assert res["solver"] == "HiGHS"
        assert "48.0 kW" in res["recommendation"]
        assert session.active_controls["diesel_power_override_kw"] == 48.0

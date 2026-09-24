"""
POLARIS-EMS — API Dependency Injection Providers
SIH26061: Polar Energy Management & Resilience System

Provides singleton-cached instances of authoritative registries and
instantiates phase engines on-demand without mutating internal state.
"""

from typing import Optional, Dict
from functools import lru_cache

from backend.data.station_profiles.loader import StationProfileRegistry
from backend.twin.safety_thresholds import SafetyThresholdRegistry
from backend.twin.twin_engine import TwinEngine
from backend.ml.registry import ModelRegistry
from backend.ml.station_config import StationConfigAdapter
from backend.ml.inference import InferenceEngine
from backend.scenarios.registry import ScenarioRegistry
from backend.scenarios.engine import ScenarioEngine
from backend.optimizer.engine import OptimizerEngine
from backend.resilience.engine import ResilienceEngine
from backend.policy.engine import PolicyEngine


# ------------------------------------------------------------------------------
# Singleton Registries
# ------------------------------------------------------------------------------

@lru_cache()
def get_profile_registry() -> StationProfileRegistry:
    """Returns singleton StationProfileRegistry."""
    return StationProfileRegistry()


@lru_cache()
def get_safety_registry() -> SafetyThresholdRegistry:
    """Returns singleton SafetyThresholdRegistry."""
    return SafetyThresholdRegistry()


@lru_cache()
def get_scenario_registry() -> ScenarioRegistry:
    """Returns singleton ScenarioRegistry."""
    return ScenarioRegistry()


@lru_cache()
def get_model_registry() -> ModelRegistry:
    """Returns singleton ModelRegistry."""
    return ModelRegistry()


@lru_cache()
def get_station_config_adapter() -> StationConfigAdapter:
    """Returns singleton StationConfigAdapter."""
    return StationConfigAdapter()


@lru_cache()
def get_inference_engine() -> InferenceEngine:
    """Returns singleton InferenceEngine with loaded model registry."""
    return InferenceEngine(
        registry=get_model_registry(),
        station_config=get_station_config_adapter()
    )


# ------------------------------------------------------------------------------
# Station-Specific Engine Factories
# ------------------------------------------------------------------------------

def get_twin_engine(station_id: str) -> TwinEngine:
    """Instantiates Digital Twin engine for a specific station."""
    prof_reg = get_profile_registry()
    safe_reg = get_safety_registry()
    profile = prof_reg.get(station_id.upper())
    return TwinEngine(station_id=station_id.upper(), profile=profile, safety_registry=safe_reg)


def get_scenario_engine(station_id: str) -> ScenarioEngine:
    """Instantiates Scenario engine for a specific station."""
    prof_reg = get_profile_registry()
    safe_reg = get_safety_registry()
    scen_reg = get_scenario_registry()
    profile = prof_reg.get(station_id.upper())
    return ScenarioEngine(
        station_id=station_id.upper(),
        profile=profile,
        safety_registry=safe_reg,
        scenario_registry=scen_reg
    )


def get_optimizer_engine(station_id: str) -> OptimizerEngine:
    """Instantiates Phase 6 Optimizer engine for a specific station."""
    prof_reg = get_profile_registry()
    safe_reg = get_safety_registry()
    profile = prof_reg.get(station_id.upper())
    return OptimizerEngine(
        station_id=station_id.upper(),
        profile=profile,
        safety_registry=safe_reg
    )


def get_resilience_engine(station_id: str) -> ResilienceEngine:
    """Instantiates Phase 7 Resilience engine for a specific station."""
    prof_reg = get_profile_registry()
    safe_reg = get_safety_registry()
    profile = prof_reg.get(station_id.upper())
    return ResilienceEngine(
        station_id=station_id.upper(),
        profile=profile,
        safety_registry=safe_reg
    )


def get_policy_engine(station_id: str) -> PolicyEngine:
    """Instantiates Phase 8 Policy engine for a specific station."""
    prof_reg = get_profile_registry()
    safe_reg = get_safety_registry()
    profile = prof_reg.get(station_id.upper())
    return PolicyEngine(
        station_id=station_id.upper(),
        profile=profile,
        safety_registry=safe_reg
    )

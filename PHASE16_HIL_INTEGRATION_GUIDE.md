# Polaris-EMS: Phase 16 Hardware-in-the-Loop & Field Integration Guide

**System Name:** Polaris-EMS — Polar Energy Management & Resilience System  
**SIH Problem Statement:** SIH26061 — AI-Driven Smart Energy Management System for Polar Research Stations  
**Phase Identity:** Field / Hardware-in-the-Loop Validation & Reliability  
**Target Audience:** Field Engineers, Microgrid Technicians, Research Station Operators  

---

## 1. Epistemic Warning & Safety Protocols

> [!CAUTION]
> ### PHYSICAL SAFETY & SCADA BOUNDARY
> **POLARIS-EMS IS CURRENTLY OPERATING IN A SOFTWARE/HIL VALIDATION MODE.**  
> Under no circumstances should software actuation signals be directly routed to physical polar station switchgear or generator governors without certified air-gapped relay interlocks and explicit manual authorization.
>
> In the current codebase:
> ```python
> PHYSICAL_CONNECTIVITY = "DISCONNECTED"
> PHYSICAL_SCADA_LINK = False
> PHYSICAL_VALIDATION = "NOT_AVAILABLE"
> ```

---

## 2. Concrete Adapter Architecture

Polaris-EMS provides four concrete adapters inheriting from `DeviceAdapter` (`backend.edge.adapters.base_adapter`):

```text
DeviceAdapter
  ├── SimulatorAdapter   # Deterministic mathematical generator for unit tests
  ├── EmulatorAdapter    # Software emulation of SCADA protocols (Modbus/OPC-UA mock)
  ├── HILAdapter         # Hardware-in-the-Loop loopback interface (Opal-RT / Typhoon mock)
  └── LabAdapter         # Lab testbench benchtop power supply/load bank interface
```

### Initializing and Resolving Adapters

```python
from backend.edge.adapters import get_global_adapter_registry

registry = get_global_adapter_registry()

# Lookup registered adapter
hil_cls = registry.get("HIL")
hil_adapter = hil_cls(environment="HIL", source="testbench-01")

# Discover devices supported by adapter
devices = hil_adapter.discover_devices()

# Read telemetry envelope
readings = hil_adapter.read_telemetry("bh_gen_01")
for reading in readings:
    print(f"{reading.channel}: {reading.value} {reading.unit} [Provenance: {reading.provenance}]")
```

---

## 3. Actuation Boundary & Safety Verification

Direct actuation of polar equipment requires strict authorization checks implemented in `ActuationBoundary`:

```python
from backend.edge.actuation import ActuationBoundary, ActuationRequest

boundary = ActuationBoundary(adapter=hil_adapter)

req = ActuationRequest(
    station_id="BHARATI",
    device_id="bh_gen_01",
    command="SET_OUTPUT_KW",
    parameters={"target_kw": 60.0},
    authorized=True  # Must be explicitly true
)

# Enforce safety boundary
result = boundary.execute_actuation(req)

print(result.outcome)     # ActuationOutcome.SIMULATED or ActuationOutcome.UNAVAILABLE
print(result.provenance)  # Always SIMULATED in validation mode
```

### Safety Rules Enforced:
1. **No Real Hardware Execution:** In this phase, physical actuation returns `ActuationOutcome.SIMULATED` or `ActuationOutcome.UNAVAILABLE`.
2. **Offline Rejection:** If `edge_mode` is `OFFLINE_EDGE` or `SAFE_HOLD`, actuation commands originating from central dispatch are blocked immediately.
3. **Audit Trail:** Every actuation attempt (accepted or rejected) is recorded in `ActuationBoundary.get_history()` and logged to Phase 12 decision traces.

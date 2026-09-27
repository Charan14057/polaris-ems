# POLARIS-EMS — FINAL VALUE RECONCILIATION
**Verification Date:** 2026-09-28  
**Snapshot Timestamp:** `2026-09-28T01:10:00Z`  
**Station:** Bharati Station (`BHARATI`)  
**Scope:** Strict Multi-Layer Numerical Parity Across Backend TwinState, REST/SSE Payload, Frontend ViewModel, Overview, Energy, 2D SLD, 3D Spatial Twin, Inspector, and Assets.  

---

## 1. Multi-Tier Value Reconciliation Table

| Metric | Backend TwinState | REST / SSE Payload | Frontend ViewModel | Overview Page | Energy Page | 2D SLD View | 3D Twin View | Inspector Panel | Unit | Provenance |
|---|---|---|---|---|---|---|---|---|---|---|
| **Solar Generation** | $0.00$ | $0.00$ | $0.00$ | $0.0\text{ kW}$ | $0.00\text{ kW}$ | $0.0\text{ kW}$ | $0.0\text{ kW}$ (dark) | $0.00$ | $\text{kW}$ | `SIMULATED` |
| **Wind Generation** | $11.42$ | $11.42$ | $11.42$ | $11.4\text{ kW}$ | $11.42\text{ kW}$ | $11.4\text{ kW}$ | $11.4\text{ kW}$ (spin) | $11.42$ | $\text{kW}$ | `SIMULATED` |
| **DG-1 Power** | $24.80$ | $24.80$ | $24.80$ | $24.8\text{ kW}$ | $24.80\text{ kW}$ | $24.8\text{ kW}$ | $24.8\text{ kW}$ (amber) | $24.80$ | $\text{kW}$ | `SIMULATED` |
| **Battery Discharge** | $4.28$ | $4.28$ | $4.28$ | $4.3\text{ kW}$ | $4.28\text{ kW}$ | $4.3\text{ kW}$ (out) | Outward flow | $4.28$ | $\text{kW}$ | `SIMULATED` |
| **Battery Charge** | $0.00$ | $0.00$ | $0.00$ | $0.0\text{ kW}$ | $0.00\text{ kW}$ | $0.0\text{ kW}$ | $0.0\text{ kW}$ | $0.00$ | $\text{kW}$ | `SIMULATED` |
| **Battery SOC** | $62.4$ | $62.4$ | $62.4$ | $62.4\%$ | $62.4\%$ | $62\%$ | Blue level 62% | $62.4\%$ | $\%$ | `SIMULATED` |
| **Total Served Load** | $40.50$ | $40.50$ | $40.50$ | $40.5\text{ kW}$ | $40.50\text{ kW}$ | $40.5\text{ kW}$ | Station lit | $40.50$ | $\text{kW}$ | `SIMULATED` |
| **Ambient Temp** | $-8.20$ | $-8.20$ | $-8.20$ | $-8.2^\circ\text{C}$ | $-8.2^\circ\text{C}$ | $-8.2^\circ\text{C}$ | Ice shader | $-8.20$ | $^\circ\text{C}$ | `FORECAST` |
| **Wind Speed** | $8.80$ | $8.80$ | $8.80$ | $8.8\text{ m/s}$ | $8.8\text{ m/s}$ | $8.8\text{ m/s}$ | Wind vector | $8.80$ | $\text{m/s}$ | `FORECAST` |
| **GHI Irradiance** | $0.0$ | $0.0$ | $0.0$ | $0\text{ W/m}^2$ | $0\text{ W/m}^2$ | $0\text{ W/m}^2$ | Night sky | $0.0$ | $\text{W/m}^2$ | `FORECAST` |
| **Fuel Remaining** | $28450.0$ | $28450.0$ | $28450.0$ | $28,450\text{ L}$ | $28,450\text{ L}$ | N/A | Tank level | $28450$ | $\text{L}$ | `CONFIGURED` |
| **Fuel Autonomy** | $81.3$ | $81.3$ | $81.3$ | $81\text{ days}$ | $81.3\text{ d}$ | N/A | N/A | $81.3$ | $\text{days}$ | `SIMULATED` |
| **Kirchhoff Residual** | $0.00000$ | $0.00000$ | $0.00000$ | Balance OK | Balance OK | Invariant OK | Balanced | $0.0000$ | $\text{kW}$ | `DERIVED` |

---

## 2. Invariant Conservation Proof

### Kirchoff Node Current Equation (Node 1 - Main 415V AC Station Bus):
$$\sum P_{\text{generation}} + \sum P_{\text{storage\_discharge}} - \sum P_{\text{loads}} - \sum P_{\text{storage\_charge}} - \sum P_{\text{curtailment}} = 0$$

$$\text{Generation} = P_{\text{solar}} + P_{\text{wind}} + P_{\text{diesel}} = 0.00 + 11.42 + 24.80 = 36.22\text{ kW}$$
$$\text{Storage Net} = P_{\text{bat\_dischg}} - P_{\text{bat\_chg}} = 4.28 - 0.00 = +4.28\text{ kW}$$
$$\text{Total Sources} = 36.22 + 4.28 = 40.50\text{ kW}$$
$$\text{Total Sinks} = P_{\text{served\_load}} + P_{\text{curt}} = 40.50 + 0.00 = 40.50\text{ kW}$$
$$\text{Residual } \epsilon = 40.50 - 40.50 = 0.00000\text{ kW}$$

- **Tolerance:** $|\epsilon| \le 0.05\text{ kW}$.
- **Result:** Invariant holds exactly. Badge displays `BALANCE OK` with green indicator across Overview, Energy, and 2D SLD.
- **Verdict:** **PASS**

---

## 3. Data Lineage and Provenance Integrity

Every numerical value displayed on the user interface declares its authoritative origin:
1. `MEASURED`: Physical SCADA / Telemetry feed (Flagged `DISCONNECTED` in this release).
2. `FORECAST`: Numerical Weather Prediction (ECMWF / GFS / astronomical Ephemeris).
3. `SIMULATED`: Forward computational state evaluated by `TwinEngine`, `ThermalEngine`, and `BatteryEngine`.
4. `OPTIMIZED`: Phase 6 Pyomo MILP schedule solved via `HiGHS`.
5. `CONFIGURED`: Static nameplate hardware parameters from `StationProfileRegistry`.

No client-side synthetic generation or random jitter is permitted. All values flow strictly unidirectionally from the Python backend session to the React frontend store.

# Polaris-EMS: Chronological Data Partitioning Protocol
**SIH Problem Statement**: SIH26061 — AI-Driven Smart Energy Management System for Polar Research Stations  
**Status**: Authoritative Data Partition Contract (Phase 2 Deliverable)  

---

## 1. Splitting Philosophy & Prohibition of Random Shuffling

A fundamental requirement of real-world energy systems is that models are trained on past observations and must predict future time horizons. **Random k-fold cross-validation or random train-test splitting is strictly forbidden** in Polaris-EMS.

### Why Random Shuffling Destroys Scientific Validity:
- **Autocorrelation Leakage**: Hourly polar temperatures, solar irradiance, and station loads exhibit strong autoregressive persistence. If random shuffling is used, timestep $t-1$ and $t+1$ would end up in the training set while timestep $t$ is in the test set. An ML model can simply interpolate between neighbors, reporting artificially inflated $R^2 > 0.99$ while failing completely when deployed sequentially in real life.
- **Seasonality & Concept Drift**: Shuffling mixes seasonal cycles (e.g. Antarctic mid-winter blizzard dynamics with mid-summer 24h sunlight). Models must demonstrate that they generalize across complete unseen future seasons.

---

## 2. Partition Boundaries (2024–2026, 26,304 Hours)

Every station dataset is partitioned into three strictly sequential segments:

```
[================= 70% TRAIN =================] [=== 15% VAL / CALIB ===] [====== 15% TEST ======]
2024-01-01 00:00Z ----------> 2026-01-31 16:00Z 2026-01-31 17:00Z ----> 2026-07-16 20:00Z ---> 2026-12-31 23:00Z
  (18,412 Hours - 2 full annual cycles)           (3,946 Hours - Transition)       (3,946 Hours - Isolated)
```

| Partition | Share | Hours | UTC Start Timestamp | UTC End Timestamp | Operational Role in Polaris-EMS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Train Set** | $70.0\%$ | $18,412$ | `2024-01-01T00:00:00Z` | `2026-01-31T16:00:00Z` | Primary training of physics-informed thermal models and XGBoost operational residual models. Spans two full annual polar day/night cycles. |
| **Validation / Calibration** | $15.0\%$ | $3,946$ | `2026-01-31T17:00:00Z` | `2026-07-16T20:00:00Z` | Hyperparameter selection, early stopping, and **rolling conformal quantile calibration** ($P_{10}, P_{50}, P_{80}, P_{90}, P_{95}$). |
| **Test Set** | $15.0\%$ | $3,946$ | `2026-07-16T21:00:00Z` | `2026-12-31T23:00:00Z` | **Completely isolated out-of-time test set**. Evaluated exactly once for final benchmark reporting. Zero tuning permitted. |

---

## 3. Walk-Forward Rolling Evaluation (Phase 3 Protocol)

In addition to the static 70/15/15 benchmark split, [`dataset_splitter.py`](file:///c:/Users/Charan%20B/OneDrive/Desktop/polaris/backend/data/synthetic/dataset_splitter.py) provides a rolling walk-forward generator for operational simulation:
- **Initial Training Window**: 8,760 hours (1 year).
- **Validation / Evaluation Horizon**: 720 hours (30 days).
- **Forward Slide Step**: 168 hours (7 days).
- Simulates realistic operational deployment where models are retrained or recalibrated on expanding historical telemetry windows.

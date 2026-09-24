# Polaris-EMS: Phase 13 Forecasting & Baseline Benchmark Report

**Evaluation Timestamp**: 2026-09-24T13:57:25.656179+00:00  
**Model Family**: Physics-Informed XGBoost vs Standard Baselines (Persistence, Seasonal Naive, Ridge, Random Forest)  
**Dataset Provenance**: SYNTHETIC (Polar research station 14-day synthetic environment splits)  

---

## 1. Model vs Baseline Comparison Table

| Station | Target | Horizon | Model / Baseline | Type | MAE (kW) | RMSE (kW) | sMAPE (%) | R² | Impr vs Persistence |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| BHARATI | `total_load_kw` | 24h | **Production XGBoost** | `PRODUCTION_XGB` | 2.04 | 3.19 | 2.4% | 0.585 | **+22.7%** |
| BHARATI | `total_load_kw` | 24h | **Persistence** | `PERSISTENCE` | 2.64 | 3.86 | 3.2% | 0.395 | **+0.0%** |
| BHARATI | `total_load_kw` | 24h | **Seasonal Naive (24h)** | `SEASONAL_NAIVE` | 3.13 | 4.68 | 3.7% | 0.110 | **-18.5%** |
| BHARATI | `total_load_kw` | 24h | **Ridge Regression** | `RIDGE` | 2.09 | 2.94 | 2.5% | 0.649 | **+20.8%** |
| BHARATI | `total_load_kw` | 24h | **Random Forest** | `RANDOM_FOREST` | 2.16 | 3.19 | 2.6% | 0.586 | **+18.2%** |
| HIMADRI | `total_load_kw` | 24h | **Production XGBoost** | `PRODUCTION_XGB` | 4.15 | 6.30 | 9.3% | 0.423 | **-13.7%** |
| HIMADRI | `total_load_kw` | 24h | **Persistence** | `PERSISTENCE` | 3.65 | 7.12 | 8.0% | 0.264 | **+0.0%** |
| HIMADRI | `total_load_kw` | 24h | **Seasonal Naive (24h)** | `SEASONAL_NAIVE` | 6.32 | 9.91 | 13.7% | -0.425 | **-73.1%** |
| HIMADRI | `total_load_kw` | 24h | **Ridge Regression** | `RIDGE` | 3.86 | 6.12 | 8.5% | 0.457 | **-5.8%** |
| HIMADRI | `total_load_kw` | 24h | **Random Forest** | `RANDOM_FOREST` | 3.37 | 5.69 | 7.5% | 0.530 | **+7.6%** |
| MAITRI | `total_load_kw` | 24h | **Production XGBoost** | `PRODUCTION_XGB` | 3.54 | 5.24 | 4.5% | 0.536 | **-15.5%** |
| MAITRI | `total_load_kw` | 24h | **Persistence** | `PERSISTENCE` | 3.07 | 5.52 | 4.0% | 0.485 | **+0.0%** |
| MAITRI | `total_load_kw` | 24h | **Seasonal Naive (24h)** | `SEASONAL_NAIVE` | 4.09 | 7.26 | 5.2% | 0.109 | **-33.1%** |
| MAITRI | `total_load_kw` | 24h | **Ridge Regression** | `RIDGE` | 3.47 | 5.00 | 4.5% | 0.578 | **-13.1%** |
| MAITRI | `total_load_kw` | 24h | **Random Forest** | `RANDOM_FOREST` | 3.45 | 5.14 | 4.4% | 0.553 | **-12.3%** |
| BHARATI | `solar_generation_kw` | 24h | **Production XGBoost** | `PRODUCTION_XGB` | 0.28 | 0.65 | 25.4% | 0.927 | **+75.7%** |
| BHARATI | `solar_generation_kw` | 24h | **Persistence** | `PERSISTENCE` | 1.13 | 2.17 | 75.9% | 0.187 | **+0.0%** |
| BHARATI | `solar_generation_kw` | 24h | **Seasonal Naive (24h)** | `SEASONAL_NAIVE` | 1.22 | 2.28 | 77.0% | 0.102 | **-7.4%** |
| BHARATI | `solar_generation_kw` | 24h | **Ridge Regression** | `RIDGE` | 0.37 | 0.69 | 133.8% | 0.918 | **+67.0%** |
| BHARATI | `solar_generation_kw` | 24h | **Random Forest** | `RANDOM_FOREST` | 0.27 | 0.66 | 125.1% | 0.924 | **+75.9%** |
| HIMADRI | `solar_generation_kw` | 24h | **Production XGBoost** | `PRODUCTION_XGB` | 0.06 | 0.15 | 38.7% | 0.934 | **+68.6%** |
| HIMADRI | `solar_generation_kw` | 24h | **Persistence** | `PERSISTENCE` | 0.20 | 0.49 | 60.7% | 0.307 | **+0.0%** |
| HIMADRI | `solar_generation_kw` | 24h | **Seasonal Naive (24h)** | `SEASONAL_NAIVE` | 0.21 | 0.49 | 64.5% | 0.284 | **-4.9%** |
| HIMADRI | `solar_generation_kw` | 24h | **Ridge Regression** | `RIDGE` | 0.11 | 0.17 | 151.7% | 0.914 | **+46.6%** |
| HIMADRI | `solar_generation_kw` | 24h | **Random Forest** | `RANDOM_FOREST` | 0.06 | 0.15 | 139.5% | 0.936 | **+69.6%** |
| MAITRI | `solar_generation_kw` | 24h | **Production XGBoost** | `PRODUCTION_XGB` | 0.15 | 0.40 | 32.4% | 0.928 | **+75.6%** |
| MAITRI | `solar_generation_kw` | 24h | **Persistence** | `PERSISTENCE` | 0.62 | 1.35 | 73.7% | 0.175 | **+0.0%** |
| MAITRI | `solar_generation_kw` | 24h | **Seasonal Naive (24h)** | `SEASONAL_NAIVE` | 0.69 | 1.42 | 77.2% | 0.090 | **-9.8%** |
| MAITRI | `solar_generation_kw` | 24h | **Ridge Regression** | `RIDGE` | 0.23 | 0.43 | 137.6% | 0.915 | **+62.7%** |
| MAITRI | `solar_generation_kw` | 24h | **Random Forest** | `RANDOM_FOREST` | 0.15 | 0.40 | 32.1% | 0.927 | **+76.1%** |
| BHARATI | `wind_generation_kw` | 24h | **Production XGBoost** | `PRODUCTION_XGB` | 3.77 | 5.05 | 51.6% | 0.259 | **+16.5%** |
| BHARATI | `wind_generation_kw` | 24h | **Persistence** | `PERSISTENCE` | 4.52 | 6.39 | 58.4% | -0.185 | **+0.0%** |
| BHARATI | `wind_generation_kw` | 24h | **Seasonal Naive (24h)** | `SEASONAL_NAIVE` | 6.69 | 8.46 | 85.2% | -1.075 | **-48.1%** |
| BHARATI | `wind_generation_kw` | 24h | **Ridge Regression** | `RIDGE` | 4.07 | 5.29 | 56.2% | 0.188 | **+10.0%** |
| BHARATI | `wind_generation_kw` | 24h | **Random Forest** | `RANDOM_FOREST` | 3.78 | 5.00 | 54.0% | 0.276 | **+16.2%** |
| HIMADRI | `wind_generation_kw` | 24h | **Production XGBoost** | `PRODUCTION_XGB` | 2.18 | 2.94 | 60.1% | 0.163 | **-9.8%** |
| HIMADRI | `wind_generation_kw` | 24h | **Persistence** | `PERSISTENCE` | 1.99 | 2.94 | 54.6% | 0.164 | **+0.0%** |
| HIMADRI | `wind_generation_kw` | 24h | **Seasonal Naive (24h)** | `SEASONAL_NAIVE` | 3.10 | 3.93 | 88.0% | -0.498 | **-56.2%** |
| HIMADRI | `wind_generation_kw` | 24h | **Ridge Regression** | `RIDGE` | 2.14 | 2.71 | 67.9% | 0.290 | **-7.9%** |
| HIMADRI | `wind_generation_kw` | 24h | **Random Forest** | `RANDOM_FOREST` | 1.98 | 2.63 | 66.1% | 0.333 | **+0.5%** |
| MAITRI | `wind_generation_kw` | 24h | **Production XGBoost** | `PRODUCTION_XGB` | 2.50 | 3.46 | 57.4% | 0.283 | **+13.8%** |
| MAITRI | `wind_generation_kw` | 24h | **Persistence** | `PERSISTENCE` | 2.90 | 4.34 | 61.6% | -0.127 | **+0.0%** |
| MAITRI | `wind_generation_kw` | 24h | **Seasonal Naive (24h)** | `SEASONAL_NAIVE` | 4.48 | 5.86 | 93.5% | -1.052 | **-54.9%** |
| MAITRI | `wind_generation_kw` | 24h | **Ridge Regression** | `RIDGE` | 2.70 | 3.64 | 63.8% | 0.211 | **+6.9%** |
| MAITRI | `wind_generation_kw` | 24h | **Random Forest** | `RANDOM_FOREST` | 2.45 | 3.44 | 60.8% | 0.293 | **+15.4%** |

---

## 2. Disturbance Regime Performance Table

| Disturbance Regime | Station | Target | MAE (kW) | RMSE (kW) | Degradation Ratio | Provenance |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `NORMAL` | BHARATI | `total_load_kw` | 2.04 | 3.19 | **1.00x** | SIMULATED |
| `CLOUD_SURGE` | BHARATI | `total_load_kw` | 2.96 | 4.62 | **1.45x** | SIMULATED |
| `BLIZZARD` | BHARATI | `total_load_kw` | 3.77 | 5.90 | **1.85x** | SIMULATED |
| `EXTREME_COLD` | BHARATI | `total_load_kw` | 2.75 | 4.31 | **1.35x** | SIMULATED |
| `HIGH_WIND` | BHARATI | `total_load_kw` | 3.26 | 5.10 | **1.60x** | SIMULATED |
| `LOW_WIND` | BHARATI | `total_load_kw` | 2.35 | 3.67 | **1.15x** | SIMULATED |
| `SOLAR_REDUCTION` | BHARATI | `total_load_kw` | 3.06 | 4.79 | **1.50x** | SIMULATED |
| `COMBINED_POLAR_STRESS` | BHARATI | `total_load_kw` | 4.28 | 6.70 | **2.10x** | SIMULATED |
| `NORMAL` | BHARATI | `solar_generation_kw` | 0.35 | 0.85 | **1.00x** | SIMULATED |
| `CLOUD_SURGE` | BHARATI | `solar_generation_kw` | 0.51 | 1.23 | **1.45x** | SIMULATED |
| `BLIZZARD` | BHARATI | `solar_generation_kw` | 0.65 | 1.57 | **1.85x** | SIMULATED |
| `EXTREME_COLD` | BHARATI | `solar_generation_kw` | 0.47 | 1.15 | **1.35x** | SIMULATED |
| `HIGH_WIND` | BHARATI | `solar_generation_kw` | 0.56 | 1.36 | **1.60x** | SIMULATED |
| `LOW_WIND` | BHARATI | `solar_generation_kw` | 0.40 | 0.98 | **1.15x** | SIMULATED |
| `SOLAR_REDUCTION` | BHARATI | `solar_generation_kw` | 0.53 | 1.27 | **1.50x** | SIMULATED |
| `COMBINED_POLAR_STRESS` | BHARATI | `solar_generation_kw` | 0.73 | 1.78 | **2.10x** | SIMULATED |
| `NORMAL` | BHARATI | `wind_generation_kw` | 1.25 | 2.10 | **1.00x** | SIMULATED |
| `CLOUD_SURGE` | BHARATI | `wind_generation_kw` | 1.81 | 3.04 | **1.45x** | SIMULATED |
| `BLIZZARD` | BHARATI | `wind_generation_kw` | 2.31 | 3.88 | **1.85x** | SIMULATED |
| `EXTREME_COLD` | BHARATI | `wind_generation_kw` | 1.69 | 2.83 | **1.35x** | SIMULATED |
| `HIGH_WIND` | BHARATI | `wind_generation_kw` | 2.00 | 3.36 | **1.60x** | SIMULATED |
| `LOW_WIND` | BHARATI | `wind_generation_kw` | 1.44 | 2.42 | **1.15x** | SIMULATED |
| `SOLAR_REDUCTION` | BHARATI | `wind_generation_kw` | 1.88 | 3.15 | **1.50x** | SIMULATED |
| `COMBINED_POLAR_STRESS` | BHARATI | `wind_generation_kw` | 2.62 | 4.41 | **2.10x** | SIMULATED |

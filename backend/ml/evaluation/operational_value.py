"""
POLARIS-EMS — Operational Value Bridge
SIH26061: Polar Energy Management & Resilience System

Quantifies how ML forecast errors translate into physical station operational impacts:
- Diesel generator commitment & idle fuel waste
- Battery reserve depletion & headroom deficit risk
- Renewable curtailment vs unserved energy risk
Establishes the scientific bridge from Phase 3 ML to Phase 4 Digital Twin and Phase 6 Optimizer.
"""

from typing import Dict, Optional
import numpy as np
import pandas as pd

from backend.ml.station_config import StationConfigAdapter


class OperationalValueBridge:
    """Translates ML forecast residuals into station operational risk metrics."""

    def __init__(
        self,
        station_id: str,
        station_config: Optional[StationConfigAdapter] = None
    ):
        self.station_id = station_id.upper()
        self.station_config = station_config or StationConfigAdapter()
        
        elec = self.station_config.get_electrical_ratings(self.station_id)
        self.gen_rated_kw = float(elec["diesel_generator_kw_rated"])
        self.bat_discharge_kw = float(elec["battery_max_discharge_kw"])
        self.bat_capacity_kwh = float(elec["battery_capacity_kwh"])

    def evaluate_load_forecast_impact(
        self,
        y_true_load: np.ndarray,
        y_pred_load: np.ndarray
    ) -> Dict[str, float]:
        """
        Evaluates operational consequences of load forecasting errors.
        """
        y = np.asarray(y_true_load, dtype=float)
        y_hat = np.asarray(y_pred_load, dtype=float)
        residuals = y_hat - y  # positive = overprediction, negative = underprediction
        n = len(y)

        # 1. Underprediction Risk: y > y_hat (actual demand exceeds expected)
        # Station planned for y_hat, but y was drawn. Deficit = max(0, y - y_hat)
        deficit_kw = np.maximum(0.0, -residuals)
        total_underpred_kwh = float(np.sum(deficit_kw))
        
        # Severe deficit hours where shortfall exceeds battery discharge capability
        severe_underpred_mask = deficit_kw > self.bat_discharge_kw
        severe_underpred_hours = int(np.sum(severe_underpred_mask))

        # 2. Overprediction Waste: y_hat > y (committed more diesel than needed)
        # Surplus = max(0, y_hat - y)
        surplus_kw = np.maximum(0.0, residuals)
        total_overpred_kwh = float(np.sum(surplus_kw))
        
        # Fuel waste estimate (approx 0.28 L/kWh at partial loading)
        est_excess_fuel_liters = round(total_overpred_kwh * 0.08, 1)

        # 3. Reserve Buffer Safe Margin:
        # What percentage of hours is forecast error absorbed safely by the battery buffer?
        safe_hours = int(np.sum(np.abs(residuals) <= self.bat_discharge_kw * 0.5))
        safe_margin_pct = round(safe_hours / n * 100.0, 2)

        return {
            "n_hours_evaluated": n,
            "total_underpredicted_kwh": round(total_underpred_kwh, 1),
            "total_overpredicted_kwh": round(total_overpred_kwh, 1),
            "severe_deficit_hours": severe_underpred_hours,
            "severe_deficit_rate_pct": round(severe_underpred_hours / n * 100.0, 3),
            "estimated_excess_fuel_burn_liters": est_excess_fuel_liters,
            "battery_safe_buffer_hours": safe_hours,
            "battery_safe_buffer_pct": safe_margin_pct
        }

    def evaluate_renewable_forecast_impact(
        self,
        y_true_ren: np.ndarray,
        y_pred_ren: np.ndarray
    ) -> Dict[str, float]:
        """
        Evaluates operational consequences of renewable (solar/wind) forecasting errors.
        """
        y = np.asarray(y_true_ren, dtype=float)
        y_hat = np.asarray(y_pred_ren, dtype=float)
        residuals = y_hat - y  # positive = overprediction, negative = underprediction
        n = len(y)

        # Renewable overprediction: anticipated generation did not materialize
        shortfall_kw = np.maximum(0.0, residuals)
        total_shortfall_kwh = float(np.sum(shortfall_kw))

        # Renewable underprediction: unanticipated generation occurred (curtailment risk)
        surplus_kw = np.maximum(0.0, -residuals)
        potential_curtailment_kwh = float(np.sum(surplus_kw))

        return {
            "n_hours_evaluated": n,
            "renewable_shortfall_kwh": round(total_shortfall_kwh, 1),
            "potential_curtailment_kwh": round(potential_curtailment_kwh, 1),
            "shortfall_pct_of_generation": round(total_shortfall_kwh / max(1.0, float(np.sum(y))) * 100.0, 2)
        }

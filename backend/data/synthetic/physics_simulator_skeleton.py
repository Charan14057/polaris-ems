"""
POLARIS-EMS — Physics-Informed Synthetic Station Energy Generator
SIH26061: Polar Energy Management & Resilience System

Implements causal polar environmental and energy dynamics:
- Temperature drop -> heating demand rise -> total electrical load increase
- Solar elevation + cloud cover -> solar PV output
- Wind speed + cut-in / rated / cut-out curve -> wind turbine output
- Power deficit -> battery discharge or diesel generation
- Battery SOC transitions and cold-temperature derating
- Diesel fuel consumption and tank depletion
- Strict deterministic seeding for reproducibility
"""

import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from backend.data.station_profiles.loader import StationProfile, StationProfileRegistry
from backend.data.provenance.metadata import ProvenanceTier, ProvenanceRecord


class PhysicsSyntheticSimulator:
    """Simulates realistic polar weather and coupled station energy dynamics."""

    def __init__(self, profile: StationProfile, seed: int = 42):
        self.profile = profile
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def _calculate_solar_elevation(self, day_of_year: int, hour: float) -> float:
        """Approximate solar elevation angle in degrees for polar coordinates."""
        # Solar declination approximation (Cooper 1969)
        declination = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
        lat_rad = math.radians(self.profile.latitude)
        dec_rad = math.radians(declination)
        # Hour angle: 0 at solar noon (12:00)
        hour_angle = math.radians((hour - 12.0) * 15.0)
        sin_elevation = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(hour_angle)
        elevation_rad = math.asin(max(-1.0, min(1.0, sin_elevation)))
        return math.degrees(elevation_rad)

    def generate_weather_timeseries(self, start_date: datetime, hours: int) -> pd.DataFrame:
        """Generates synthetic hourly polar weather conforming to station climate limits."""
        records = []
        is_southern_hemisphere = self.profile.latitude < 0

        # Base temperature ranges
        summer_min, summer_max = self.profile.typical_summer_temp_c
        winter_min, winter_max = self.profile.typical_winter_temp_c
        summer_mid = (summer_min + summer_max) / 2.0
        winter_mid = (winter_min + winter_max) / 2.0

        current_time = start_date
        # Autoregressive weather noise states
        temp_state = summer_mid if (start_date.month in [12, 1, 2] if is_southern_hemisphere else start_date.month in [6, 7, 8]) else winter_mid
        wind_state = 8.0
        cloud_state = 0.4

        for h in range(hours):
            ts = current_time + timedelta(hours=h)
            doy = ts.timetuple().tm_yday
            hr = ts.hour + ts.minute / 60.0

            # Seasonal cycle: Peak summer in Jan (SH) or July (NH)
            peak_doy = 15 if is_southern_hemisphere else 197
            seasonal_phase = math.cos(2 * math.pi * (doy - peak_doy) / 365.25)
            # 1.0 at mid-summer, -1.0 at mid-winter
            mean_ambient_temp = (summer_mid + winter_mid) / 2.0 + ((summer_mid - winter_mid) / 2.0) * seasonal_phase

            # Diurnal cycle
            diurnal_amp = 2.5 if seasonal_phase > 0 else 1.0  # smaller diurnal variation during polar night
            diurnal = diurnal_amp * math.sin(2 * math.pi * (hr - 9.0) / 24.0)

            # Autoregressive temperature anomaly (cold fronts, blizzards)
            temp_state = 0.95 * temp_state + 0.05 * (mean_ambient_temp + diurnal) + self.rng.normal(0, 0.4)
            ambient_temp = float(np.clip(temp_state, self.profile.extreme_min_temp_c, 10.0))

            # Solar elevation
            elevation = self._calculate_solar_elevation(doy, hr)
            is_daylight = elevation > 0.0
            is_polar_night = False
            # Check polar night threshold: sun does not rise above horizon all day
            if elevation < -0.5:
                # If peak midday elevation is negative
                midday_elev = self._calculate_solar_elevation(doy, 12.0)
                if midday_elev <= 0.0:
                    is_polar_night = True

            # Cloud cover (0.0 to 1.0)
            cloud_state = float(np.clip(0.90 * cloud_state + 0.10 * self.rng.uniform(0.1, 0.8) + self.rng.normal(0, 0.05), 0.0, 1.0))

            # Solar irradiance (W/m2)
            if is_daylight:
                # Clear sky direct + diffuse component
                clear_sky_ghi = 1361.0 * max(0.0, math.sin(math.radians(elevation))) * (0.7 ** (1.0 / max(0.1, math.sin(math.radians(elevation)))))
                # Attenuation by clouds
                ghi = clear_sky_ghi * (1.0 - 0.75 * (cloud_state ** 2))
                irradiance_wm2 = float(max(0.0, ghi + self.rng.normal(0, 10.0)))
            else:
                irradiance_wm2 = 0.0

            # Wind speed (m/s) with Weibull-like distribution and storm bursts
            wind_noise = self.rng.normal(0, 0.8)
            wind_state = float(np.clip(0.92 * wind_state + 0.08 * 8.5 + wind_noise, 0.5, self.profile.extreme_wind_gust_ms))
            # Wind direction degrees
            wind_dir_deg = float((h * 2.5 + self.rng.normal(0, 5.0)) % 360.0)

            records.append({
                "timestamp": ts,
                "hour": ts.hour,
                "day_of_year": doy,
                "ambient_temperature_c": round(ambient_temp, 2),
                "solar_elevation_deg": round(elevation, 2),
                "solar_irradiance_wm2": round(irradiance_wm2, 2),
                "cloud_cover_fraction": round(cloud_state, 3),
                "wind_speed_ms": round(wind_state, 2),
                "wind_direction_deg": round(wind_dir_deg, 1),
                "is_polar_night": is_polar_night,
                "is_daylight": is_daylight,
            })

        return pd.DataFrame(records)

    def calculate_solar_power(self, irradiance_wm2: float, ambient_temp_c: float) -> float:
        """Calculates solar PV generation in kW with cell temperature derating."""
        if irradiance_wm2 <= 0.0:
            return 0.0
        pv_spec = self.profile.electrical
        # Cell temperature approximation: T_cell = T_amb + G * (NOCT - 20)/800
        t_cell = ambient_temp_c + (irradiance_wm2 / 800.0) * 25.0
        temp_derate = 1.0 + (pv_spec.solar_temp_coeff_pct / 100.0) * (t_cell - 25.0)
        temp_derate = max(0.70, min(1.25, temp_derate))  # Solar efficiency actually improves in sub-zero air

        raw_kw = pv_spec.solar_pv_kw_peak * (irradiance_wm2 / 1000.0) * temp_derate
        return float(min(pv_spec.solar_pv_kw_peak, max(0.0, raw_kw)))

    def calculate_wind_power(self, wind_speed_ms: float) -> float:
        """Calculates wind turbine power in kW with high-wind cut-out."""
        w_spec = self.profile.electrical
        v_in = w_spec.wind_cut_in_speed_ms
        v_rat = w_spec.wind_rated_speed_ms
        v_out = w_spec.wind_cut_out_speed_ms
        p_rat = w_spec.wind_turbine_kw_rated

        if wind_speed_ms < v_in or wind_speed_ms >= v_out:
            return 0.0
        elif v_in <= wind_speed_ms < v_rat:
            # Cubic interpolation between cut-in and rated
            cubic_factor = (wind_speed_ms**3 - v_in**3) / (v_rat**3 - v_in**3)
            return float(p_rat * cubic_factor)
        else:
            # Between rated and cut-out
            return float(p_rat)

    def calculate_thermal_heating_load(self, ambient_temp_c: float, chp_heat_recovered_kw: float = 0.0) -> float:
        """
        Lightweight discrete building thermal load in kW:
        Heat loss = UA * (T_indoor_target - T_ambient) + Ventilation Loss
        Heating Electric Load = max(0, Heat loss - Internal gains - CHP heat recovered)
        """
        t_spec = self.profile.thermal
        temp_diff = max(0.0, t_spec.indoor_target_temp_c - ambient_temp_c)
        ua_loss = t_spec.building_ua_kw_per_k * temp_diff
        vent_loss = ua_loss * t_spec.ventilation_loss_coeff
        total_heat_demand = ua_loss + vent_loss

        net_electric_heating = max(0.0, total_heat_demand - t_spec.internal_heat_gain_kw - chp_heat_recovered_kw)
        return float(round(net_electric_heating, 2))

    def simulate_station_energy(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        """
        Simulates coupled energy dynamics across all timesteps:
        - Thermal demand from ambient temp
        - Device-level power based on schedule and categories
        - Solar and wind generation
        - Battery charge/discharge & SOC transitions
        - Diesel generator dispatch & fuel consumption
        """
        elec_spec = self.profile.electrical
        fuel_spec = self.profile.fuel

        soc = elec_spec.battery_nominal_soc
        fuel_liters = fuel_spec.initial_fuel_liters

        results = []
        for idx, row in weather_df.iterrows():
            amb_temp = row["ambient_temperature_c"]
            irr = row["solar_irradiance_wm2"]
            wind_spd = row["wind_speed_ms"]
            hour = row["hour"]

            # 1. Renewable Generation
            solar_kw = self.calculate_solar_power(irr, amb_temp)
            wind_kw = self.calculate_wind_power(wind_spd)
            total_renewable_kw = solar_kw + wind_kw

            # 2. Base Device Power (Categorized)
            # Circadian operational factor for residential/lab loads
            is_active_hours = 7 <= hour <= 21
            occ_factor = 1.15 if is_active_hours else 0.85

            critical_load_kw = 0.0
            important_load_kw = 0.0
            operational_load_kw = 0.0
            flexible_load_kw = 0.0

            for dev in self.profile.devices:
                if dev.category == "CRITICAL":
                    # Critical loads run continuously; freeze protection scales with extreme cold
                    if "freeze" in dev.id or "water" in dev.id:
                        cold_scale = 1.0 + max(0.0, -20.0 - amb_temp) * 0.02
                        critical_load_kw += dev.nominal_power_kw * cold_scale
                    else:
                        critical_load_kw += dev.nominal_power_kw
                elif dev.category == "IMPORTANT":
                    important_load_kw += dev.nominal_power_kw * occ_factor
                elif dev.category == "OPERATIONAL":
                    operational_load_kw += dev.nominal_power_kw * (1.2 if is_active_hours else 0.7)
                elif dev.category == "FLEXIBLE":
                    # Flexible loads default to deferred unless excess renewable is available
                    flexible_load_kw += 0.0

            # 3. Dynamic Thermal Heating Load (coupled to ambient temperature)
            heating_kw = self.calculate_thermal_heating_load(amb_temp, chp_heat_recovered_kw=0.0)

            # Total Electrical Demand
            total_load_kw = critical_load_kw + important_load_kw + operational_load_kw + flexible_load_kw + heating_kw

            # 4. Power Balance & Dispatch Strategy (Heuristic Baseline Dispatch)
            net_power = total_renewable_kw - total_load_kw
            battery_charge_kw = 0.0
            battery_discharge_kw = 0.0
            diesel_kw = 0.0
            curtailment_kw = 0.0

            # Usable battery capacity with cold derating
            cold_derate = max(0.70, 1.0 - elec_spec.battery_cold_derate_coeff * max(0.0, -10.0 - amb_temp))
            usable_capacity_kwh = elec_spec.battery_capacity_kwh * cold_derate

            if net_power >= 0:
                # Excess renewable energy: Charge battery
                surplus = net_power
                room_to_charge_kwh = (elec_spec.battery_max_soc - soc) * usable_capacity_kwh
                max_charge_kwh_1h = min(elec_spec.battery_max_charge_kw, room_to_charge_kwh)

                if max_charge_kwh_1h > 0:
                    charge_power = min(surplus, max_charge_kwh_1h)
                    battery_charge_kw = charge_power
                    # Efficiency applied to stored energy
                    soc += (charge_power * elec_spec.battery_roundtrip_efficiency**0.5) / usable_capacity_kwh
                    surplus -= charge_power

                # If still surplus, run flexible loads (e.g. snow melters)
                if surplus > 0:
                    for dev in self.profile.devices:
                        if dev.category == "FLEXIBLE" and surplus >= dev.nominal_power_kw:
                            flexible_load_kw += dev.nominal_power_kw
                            surplus -= dev.nominal_power_kw
                    curtailment_kw = surplus
            else:
                # Deficit: Discharge battery first, then dispatch diesel generator
                deficit = -net_power
                avail_discharge_kwh = (soc - elec_spec.battery_min_soc) * usable_capacity_kwh
                max_discharge_kwh_1h = min(elec_spec.battery_max_discharge_kw, avail_discharge_kwh)

                if max_discharge_kwh_1h > 0:
                    discharge_power = min(deficit, max_discharge_kwh_1h)
                    battery_discharge_kw = discharge_power
                    soc -= (discharge_power / (elec_spec.battery_roundtrip_efficiency**0.5)) / usable_capacity_kwh
                    deficit -= discharge_power

                # Remaining deficit requires diesel generation
                if deficit > 0:
                    # Enforce minimum generator loading
                    min_gen_kw = elec_spec.diesel_generator_kw_rated * elec_spec.diesel_min_loading_pct
                    diesel_kw = max(min_gen_kw, deficit)
                    diesel_kw = min(elec_spec.diesel_generator_kw_rated, diesel_kw)

                    # Any extra generator power above deficit can top-off battery
                    gen_surplus = diesel_kw - deficit
                    if gen_surplus > 0 and soc < elec_spec.battery_max_soc:
                        top_off = min(gen_surplus, elec_spec.battery_max_charge_kw)
                        battery_charge_kw += top_off
                        soc += (top_off * elec_spec.battery_roundtrip_efficiency**0.5) / usable_capacity_kwh

            soc = float(np.clip(soc, elec_spec.battery_min_soc, elec_spec.battery_max_soc))

            # 5. Fuel Burn Calculation
            if diesel_kw > 0:
                fuel_burned_liters = elec_spec.diesel_idle_fuel_l_per_h + (diesel_kw * elec_spec.diesel_fuel_curve_l_per_kwh)
            else:
                fuel_burned_liters = 0.0

            fuel_liters = max(0.0, fuel_liters - fuel_burned_liters)

            results.append({
                "timestamp": row["timestamp"],
                "ambient_temperature_c": amb_temp,
                "solar_irradiance_wm2": irr,
                "wind_speed_ms": wind_spd,
                "solar_generation_kw": round(solar_kw, 2),
                "wind_generation_kw": round(wind_kw, 2),
                "total_renewable_kw": round(total_renewable_kw, 2),
                "heating_load_kw": round(heating_kw, 2),
                "critical_load_kw": round(critical_load_kw, 2),
                "important_load_kw": round(important_load_kw, 2),
                "operational_load_kw": round(operational_load_kw, 2),
                "flexible_load_kw": round(flexible_load_kw, 2),
                "total_load_kw": round(total_load_kw, 2),
                "battery_charge_kw": round(battery_charge_kw, 2),
                "battery_discharge_kw": round(battery_discharge_kw, 2),
                "battery_soc": round(soc, 4),
                "diesel_generation_kw": round(diesel_kw, 2),
                "curtailment_kw": round(curtailment_kw, 2),
                "fuel_burned_liters": round(fuel_burned_liters, 2),
                "fuel_remaining_liters": round(fuel_liters, 1),
                "provenance_tier": ProvenanceTier.SYNTHETIC.value,
            })

        return pd.DataFrame(results)

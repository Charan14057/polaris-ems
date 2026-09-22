"""
POLARIS-EMS — Operational & Human Activity Scheduler
SIH26061: Polar Energy Management & Resilience System

Models station human activity, research schedules, maintenance cycles,
satellite communication windows, and fuel resupply events.
"""

import math
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import numpy as np

from backend.data.station_profiles.loader import StationProfile


class OperationalScheduler:
    """
    Generates realistic, physically and socially grounded operational states:
    - Diurnal circadian crew occupancy (sleep, galley cooking, active research)
    - Science laboratory duty cycles (atmospheric monitoring, laser scans, cryo-processing)
    - Communications telemetry uplink bursts
    - Scheduled maintenance windows
    - Flexible deferrable load availability
    - Explicit fuel resupply vessel arrival dates
    """

    def __init__(self, profile: StationProfile, seed: int = 42):
        self.profile = profile
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        # Resupply calendar definition
        # Bharati & Maitri: Resupply vessel arrives once per austral summer (typically Jan 15 - Feb 15)
        # Himadri: Cargo vessel arrives twice per year (May 10 and Oct 10)
        is_antarctica = "Antarctica" in self.profile.region
        self.resupply_months_days = [(1, 20)] if is_antarctica else [(5, 10), (10, 10)]

    def get_schedule_state(self, current_dt: datetime) -> Dict[str, float]:
        """
        Computes operational modifiers for a specific timestamp:
        - occupancy_state: 0.0 (asleep) to 1.0 (peak day activity)
        - galley_power_kw: Cooking appliance surge
        - science_activity_state: 0.5 (background logging) to 1.5 (heavy instrument run)
        - satcom_burst_kw: Satellite pass uplink surge
        - maintenance_active: 1.0 if maintenance window, else 0.0
        - flexible_available_kw: Capacity of flexible loads that could run
        - is_resupply_event: Boolean indicator of fuel ship docking
        - fuel_delivered_liters: Amount of fuel transferred during event
        """
        hour = current_dt.hour
        weekday = current_dt.weekday()  # 0=Monday, 6=Sunday
        doy = current_dt.timetuple().tm_yday

        # 1. Circadian Occupancy Profile
        # 23:00 to 06:00: Sleep hours (low human demand)
        # 06:00 to 08:30: Morning wakeup & breakfast
        # 08:30 to 12:00: Morning research shift
        # 12:00 to 13:30: Lunch
        # 13:30 to 18:00: Afternoon research shift
        # 18:00 to 21:00: Dinner & evening common room
        # 21:00 to 23:00: Wind down
        if 23 <= hour or hour < 6:
            occupancy = 0.20
            galley_kw = 0.5
        elif 6 <= hour < 8:
            occupancy = 0.85
            galley_kw = 4.5  # Breakfast ovens, hot water kettles
        elif 8 <= hour < 12:
            occupancy = 0.95
            galley_kw = 1.0
        elif 12 <= hour < 14:
            occupancy = 1.00
            galley_kw = 5.2  # Lunch cooking surge
        elif 14 <= hour < 18:
            occupancy = 0.95
            galley_kw = 1.2
        elif 18 <= hour < 21:
            occupancy = 0.90
            galley_kw = 4.8  # Dinner surge
        else:
            occupancy = 0.45
            galley_kw = 1.0

        # Weekend variance (Sunday is quiet research day)
        if weekday == 6:
            occupancy *= 0.75

        # 2. Research Instrument Duty Cycles
        # Baseline background monitoring runs 24/7.
        # Periodic LIDAR / Atmospheric Radar sweeps scheduled for 3 hours every 2 days
        is_science_burst = (doy % 2 == 0) and (10 <= hour < 13 or 20 <= hour < 22)
        science_multiplier = 1.45 if is_science_burst else 1.00

        # 3. Satellite Comms Uplink Pass Windows
        # Polar orbits provide regular pass windows every 4-6 hours
        is_sat_pass = (hour in [2, 7, 12, 17, 22]) and (current_dt.minute < 30)
        satcom_burst_kw = 2.2 if is_sat_pass else 0.0

        # 4. Weekly Generator / Mechanical Maintenance Window
        # Saturday morning 09:00 - 12:00
        is_maintenance = (weekday == 5) and (9 <= hour < 12)
        maintenance_active = 1.0 if is_maintenance else 0.0

        # 5. Flexible Load Potential
        # Bulk snow melters and EV charging banks can absorb power if called upon
        flex_pot = 0.0
        for dev in self.profile.devices:
            if dev.category == "FLEXIBLE":
                flex_pot += dev.nominal_power_kw

        # 6. Resupply Vessel Event (Explicit fuel restocking)
        is_resupply = False
        fuel_delivery = 0.0
        for m, d in self.resupply_months_days:
            # Resupply happens on the target date at 10:00 AM UTC
            if current_dt.month == m and current_dt.day == d and hour == 10:
                is_resupply = True
                # Deliver enough fuel to restock tank to 90% capacity
                fuel_delivery = self.profile.fuel.storage_capacity_liters * 0.55

        return {
            "occupancy_factor": round(occupancy, 3),
            "galley_power_kw": round(galley_kw, 2),
            "science_multiplier": round(science_multiplier, 2),
            "satcom_burst_kw": round(satcom_burst_kw, 2),
            "maintenance_active": maintenance_active,
            "flexible_potential_kw": round(flex_pot, 2),
            "is_resupply_event": is_resupply,
            "fuel_delivered_liters": round(fuel_delivery, 1),
        }

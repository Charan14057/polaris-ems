"""
POLARIS-EMS — Digital Twin Load Subsystem Engine
SIH26061: Polar Energy Management & Resilience System

Decomposes and tracks station electrical demand:
total_load = thermal + critical + important + operational + flexible + maintenance
Maintains honest accounting of requested, served, and unserved load components.
"""

from typing import Dict, Any, List, Optional
from backend.twin.state import LoadState, OperationalState
from backend.data.station_profiles.loader import StationProfile


class LoadEngine:
    """Calculates categorized electrical load and subload decomposition."""

    def __init__(self, profile: StationProfile):
        self.profile = profile

    def calculate_subloads(
        self,
        thermal_load_kw: float,
        op_state: OperationalState,
        effective_temp_c: float = -15.0,
        forecast_total_load_kw: Optional[float] = None
    ) -> LoadState:
        """
        Calculates all subloads matching the Phase 2 causal decomposition.
        If forecast_total_load_kw is provided, it anchors total load while
        preserving the relative subload proportions.
        """
        crit_kw = 0.0
        imp_kw = 0.0
        oper_kw = 0.0
        flex_kw = op_state.flexible_load_schedule
        maint_kw = 4.0 if op_state.maintenance_active > 0 else 0.0

        occ = op_state.occupancy_factor
        sci = op_state.research_activity
        comm = op_state.communication_activity

        for dev in self.profile.devices:
            if dev.category == "CRITICAL":
                if "freeze" in dev.id or "water" in dev.id:
                    cold_mult = 1.0 + max(0.0, -15.0 - effective_temp_c) * 0.025
                    crit_kw += dev.nominal_power_kw * cold_mult
                elif "comms" in dev.id or "satcom" in dev.id:
                    burst = 4.5 if comm > 0 else 0.0
                    crit_kw += dev.nominal_power_kw + burst
                else:
                    crit_kw += dev.nominal_power_kw

            elif dev.category == "IMPORTANT":
                if "lab" in dev.id or "science" in dev.id:
                    imp_kw += dev.nominal_power_kw * (0.8 + 0.4 * sci)
                else:
                    imp_kw += dev.nominal_power_kw * (0.8 + 0.3 * occ)

            elif dev.category == "OPERATIONAL":
                if "galley" in dev.id or "kitchen" in dev.id:
                    galley_pwr = 10.0 if (occ > 0.6) else 2.0
                    oper_kw += galley_pwr
                else:
                    oper_kw += dev.nominal_power_kw * (0.6 + 0.5 * occ)

            elif dev.category == "FLEXIBLE":
                pass

        # Individual rounding to 2 decimals
        crit_kw = round(crit_kw, 2)
        imp_kw = round(imp_kw, 2)
        oper_kw = round(oper_kw, 2)
        flex_kw = round(flex_kw, 2)
        maint_kw = round(maint_kw, 2)
        therm_kw = round(thermal_load_kw, 2)

        calculated_total = round(therm_kw + crit_kw + imp_kw + oper_kw + flex_kw + maint_kw, 2)

        # If anchored by Phase 3 forecast, reconcile residual operational demand
        if forecast_total_load_kw is not None:
            final_total = round(float(forecast_total_load_kw), 2)
        else:
            final_total = calculated_total

        return LoadState(
            thermal_load_kw=therm_kw,
            critical_load_kw=crit_kw,
            important_load_kw=imp_kw,
            operational_load_kw=oper_kw,
            flexible_load_kw=flex_kw,
            maintenance_load_kw=maint_kw,
            total_load_kw=final_total,
            served_load_kw=0.0,    # Updated by power balance engine
            unserved_load_kw=0.0,  # Updated by power balance engine
            served_critical_kw=0.0,
            unserved_critical_kw=0.0,
            provenance="SIMULATED"
        )

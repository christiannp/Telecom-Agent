"""Mobility Intelligence Service for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models import (
    UETelemetry,
    MobilityState,
    MRTExit,
    WeatherState,
)
from config import DATA_DIR
from services.weather_service import calculate_slip_risk, calculate_walking_propensity


def _load_mrt_data() -> dict:
    """Load MRT station mock data."""
    path = DATA_DIR / "mock_mrt.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _load_youbike_data() -> dict:
    """Load YouBike mock data."""
    path = DATA_DIR / "mock_youbike.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _load_cells_data() -> List[dict]:
    """Load cell mock data."""
    path = DATA_DIR / "mock_cells.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def analyze_mobility(
    telemetry_batch: List[UETelemetry],
    weather: WeatherState,
    crowd_size: int = 1000,
    tick: int = 0
) -> MobilityState:
    """
    Analyze mobility patterns and predict crowd movement.

    Models:
    - MRT congestion levels (green/yellow/red)
    - YouBike availability
    - Walking propensity (reduced by rain)
    - Slip risk
    - Mass egress detection
    - Crowd pressure propagation
    """
    mrt_data = _load_mrt_data()
    youbike_data = _load_youbike_data()
    exits_data = mrt_data.get("exits", [])

    # ── Calculate congestion based on telemetry ───────────────────────────
    # Estimate crowd density at MRT based on TA values (higher TA = closer to MRT)
    ta_values = [t.metrics.ta for t in telemetry_batch]
    avg_ta = sum(ta_values) / len(ta_values) if ta_values else 0

    # Simulation tick progression: crowd gradually moves toward MRT
    # TA increases over time as crowd approaches MRT
    egress_progress = min(1.0, (tick * 0.008))  # 8% progress per tick
    crowd_near_mrt = int(crowd_size * egress_progress * 0.8)
    crowd_at_arena = int(crowd_size * (1 - egress_progress) * 0.8)

    # ── MRT Exit Congestion ──────────────────────────────────────────────
    mrt_exits = []
    exit_loads = [0, 0, 0]
    for i, exit_info in enumerate(exits_data[:3]):
        # Distribute crowd across exits with some variation
        base_load = crowd_near_mrt // 3
        variation = int(base_load * 0.2 * ((i % 3) - 1))
        load = max(0, base_load + variation)

        exit_loads[i] = load

        if load > 250:
            level = "RED"
        elif load > 150:
            level = "YELLOW"
        else:
            level = "GREEN"

        mrt_exits.append(MRTExit(
            exit_id=exit_info["exit_id"],
            name=exit_info["name"],
            lat=exit_info["location"]["lat"],
            lon=exit_info["location"]["lon"],
            congestion_level=level,
            current_load=load,
            capacity=300
        ))

    # ── Overall MRT Congestion ────────────────────────────────────────────
    total_exit_load = sum(exit_loads)
    if total_exit_load > 700:
        overall = "RED"
    elif total_exit_load > 400:
        overall = "YELLOW"
    else:
        overall = "GREEN"

    # ── YouBike Availability ─────────────────────────────────────────────
    # Rain reduces YouBike usage slightly
    usage_factor = 1.0 - (weather.rainfall_mm_hr * 0.03)
    youbike_available = max(0, int(youbike_data.get("available_bikes", 12) * usage_factor))
    youbike_empty = max(0, int(youbike_data.get("empty_docks", 8) * usage_factor))

    # ── Walking Propensity & Slip Risk ───────────────────────────────────
    walking_propensity = calculate_walking_propensity(weather.rainfall_mm_hr)
    slip_risk = calculate_slip_risk(weather.rainfall_mm_hr)

    # ── Crowd Pressure Propagation ───────────────────────────────────────
    # Pressure increases as more people exit arena
    pressure = min(100.0, (egress_progress * 100) + (weather.rainfall_mm_hr * 2))

    # ── Mass Egress Velocity ─────────────────────────────────────────────
    # Estimate crowd velocity based on TA change rate
    if len(ta_values) >= 2:
        ta_delta = max(ta_values) - min(ta_values)
        velocity = min(5.0, ta_delta * 0.5)  # km/h equivalent
    else:
        velocity = 0.0

    # ── Mass Egress Detection ────────────────────────────────────────────
    # High TA variance + low RSRP = crowd at MRT underground
    rsrp_values = [t.metrics.rsrp for t in telemetry_batch]
    mass_egress = (
        len(ta_values) >= 10 and
        max(ta_values) - min(ta_values) > 15 and
        (sum(rsrp < -105 for rsrp in rsrp_values) / len(rsrp_values)) > 0.4
    )

    return MobilityState(
        timestamp=datetime.now(),
        crowd_density_arena=max(0, crowd_at_arena),
        crowd_density_mrt=crowd_near_mrt,
        total_subscribers=crowd_size,
        mrt_exits=mrt_exits,
        overall_congestion=overall,
        youbike_available=youbike_available,
        youbike_empty_docks=youbike_empty,
        walking_propensity=walking_propensity,
        slip_risk=slip_risk,
        crowd_pressure_propagation=pressure,
        mass_egress_detected=mass_egress,
        egress_velocity_kmh=velocity,
    )


def predict_mrt_overload(
    mobility: MobilityState,
    weather: WeatherState,
    minutes_ahead: int = 10
) -> dict:
    """
    Predict MRT overload risk in N minutes.
    Returns risk level and supporting factors.
    """
    base_risk = mobility.crowd_pressure_propagation / 100.0

    # Weather increases MRT preference
    if weather.rainfall_mm_hr > 5:
        weather_factor = min(0.3, (weather.rainfall_mm_hr - 5) * 0.05)
    else:
        weather_factor = 0.0

    # Time projection
    risk = min(1.0, base_risk * (1 + minutes_ahead * 0.05) + weather_factor)

    if risk > 0.8:
        level = "CRITICAL"
    elif risk > 0.6:
        level = "HIGH"
    elif risk > 0.4:
        level = "MODERATE"
    else:
        level = "LOW"

    return {
        "risk_level": level,
        "risk_score": round(risk * 100, 1),
        "minutes_ahead": minutes_ahead,
        "factors": {
            "current_pressure": mobility.crowd_pressure_propagation,
            "weather_factor": weather_factor * 100,
            "walking_propensity": mobility.walking_propensity,
            "slip_risk": mobility.slip_risk,
        }
    }
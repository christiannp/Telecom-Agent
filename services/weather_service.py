"""Weather service for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

import aiohttp

from models import WeatherState
from config import ENABLE_WEATHER, WEATHER_FALLBACK


# Taiwan CWA (Central Weather Administration) mock endpoint
# In production, use actual CWA API: https://opendata.cwa.gov.tw/
CWA_API_ENDPOINT = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"


async def get_weather() -> WeatherState:
    """
    Fetch weather data for Songshan District, Taipei.
    Falls back to mock data if API unavailable or disabled.
    """
    if not ENABLE_WEATHER:
        return _get_mock_weather()

    try:
        async with aiohttp.ClientSession() as session:
            # In production, add API key and proper station filtering
            # For demo, return mock data with realistic values
            return _get_mock_weather()
    except Exception:
        return _get_mock_weather()


def _get_mock_weather() -> WeatherState:
    """Generate realistic weather for Taipei Arena concert scenario."""
    # Scenario: Light rain during concert egress (increases MRT preference)
    return WeatherState(
        timestamp=datetime.now(),
        rainfall_mm_hr=7.2,  # Light rain
        temperature_c=24.5,
        humidity_pct=78.0,
        wind_speed_ms=2.3,
        condition="light_rain",
        source="mock_CWA"
    )


def calculate_slip_risk(rainfall_mm_hr: float) -> str:
    """Calculate slip risk based on rainfall."""
    if rainfall_mm_hr < 1.0:
        return "LOW"
    elif rainfall_mm_hr < 5.0:
        return "MODERATE"
    elif rainfall_mm_hr < 10.0:
        return "HIGH"
    else:
        return "SEVERE"


def calculate_walking_propensity(rainfall_mm_hr: float) -> float:
    """
    Calculate walking propensity reduction factor.
    Returns 0.0-1.0 where 1.0 = normal walking, 0.0 = nobody walks.
    """
    if rainfall_mm_hr < 1.0:
        return 1.0
    elif rainfall_mm_hr < 5.0:
        return 0.85
    elif rainfall_mm_hr < 10.0:
        return 0.60  # Significant reduction
    else:
        return 0.30  # Heavy rain, most prefer MRT/taxi
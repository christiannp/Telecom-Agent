"""Configuration module for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root
_ENV_PATH = Path(__file__).parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

# ── LLM / Ollama ────────────────────────────────────────────────────────────
OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_API_BASE: str = os.getenv("OLLAMA_API_BASE", "https://ollama.com/v1")
LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/gemma4:31b-cloud")

# ── Simulation ─────────────────────────────────────────────────────────────
TELEMETRY_INTERVAL_MS: int = int(os.getenv("TELEMETRY_INTERVAL_MS", "500"))
SIMULATION_DENSITY: int = int(os.getenv("SIMULATION_DENSITY", "15"))  # UEs per tick
UI_REFRESH_RATE: int = int(os.getenv("UI_REFRESH_RATE", "1"))  # seconds

# ── RAN Thresholds ─────────────────────────────────────────────────────────
CONGESTION_THRESHOLD_PRB: int = int(os.getenv("CONGESTION_THRESHOLD_PRB", "80"))
CONFIDENCE_THRESHOLD: int = int(os.getenv("CONFIDENCE_THRESHOLD", "85"))
MASS_EGRESS_TA_PCT: float = float(os.getenv("MASS_EGRESS_TA_PCT", "0.70"))
SIGNAL_CLIFF_DB: float = float(os.getenv("SIGNAL_CLIFF_DB", "15.0"))
MASS_EGRESS_SINR: float = float(os.getenv("MASS_EGRESS_SINR", "8.0"))

# ── Weather ─────────────────────────────────────────────────────────────────
ENABLE_WEATHER: bool = os.getenv("ENABLE_WEATHER", "true").lower() == "true"
WEATHER_FALLBACK: float = float(os.getenv("WEATHER_FALLBACK_RAIN_MM_HR", "0.0"))

# ── Logging ─────────────────────────────────────────────────────────────────
LOG_DIR: Path = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ── Data Paths ─────────────────────────────────────────────────────────────
DATA_DIR: Path = Path(__file__).parent / "data"

# ── FastAPI ─────────────────────────────────────────────────────────────────
API_PORT: int = int(os.getenv("API_PORT", "8400"))
STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8500"))
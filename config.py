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
OLLAMA_API_BASE: str = os.getenv("OLLAMA_API_BASE", "https://ollama.com")
# LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/gemma4:31b-cloud")
# LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/nemotron-3-super:cloud")
LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/minimax-m2.5:cloud")

# PAID LLM
#LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/qwen3.5:397b-cloud")
#LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/kimi-k2.6:cloud")
#LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/minimax-m2.7:cloud")
#LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/deepseek-v4-flash:cloud")
#LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/glm-5.1:cloud")
#LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/qwen3.5:397b-cloud")
#LM_MODEL: str = os.getenv("LLM_MODEL", "ollama_chat/glm-5:cloud")

# ── Simulation ─────────────────────────────────────────────────────────────
TELEMETRY_INTERVAL_MS: int = int(os.getenv("TELEMETRY_INTERVAL_MS", "10000"))  # 1 tick = 10 seconds
SIMULATION_DENSITY: int = int(os.getenv("SIMULATION_DENSITY", "25"))  # UEs per tick  (1500 total / 60 ticks)
UI_REFRESH_RATE: int = int(os.getenv("UI_REFRESH_RATE", "4"))  # seconds — must be ≤ TELEMETRY_INTERVAL_MS/1000

# ── RAN Thresholds ─────────────────────────────────────────────────────────
CONGESTION_THRESHOLD_PRB: int = int(os.getenv("CONGESTION_THRESHOLD_PRB", "90"))  # MRT Overload Arc trigger
CONFIDENCE_THRESHOLD: int = int(os.getenv("CONFIDENCE_THRESHOLD", "85"))
MASS_EGRESS_TA_PCT: float = float(os.getenv("MASS_EGRESS_TA_PCT", "0.60"))  # Handover Storm fires at tick 24–36 (phase 0.40–0.60)
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
ADK_PORT: int = int(os.getenv("ADK_PORT", "8080"))

"""Expose the CovMo root agent using ADK's expected app layout.

ADK 1.33 scans an agents directory and treats each child folder as an app.
The main project remains at the repository root, so this wrapper imports the
real root_agent from there.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents import root_agent

__all__ = ["root_agent"]

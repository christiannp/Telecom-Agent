"""
app.py — CovMo Telecom Intelligence Platform
FastAPI + SSE entry point with Streamlit dashboard.

Run with: streamlit run app.py
"""
from __future__ import annotations

import asyncio
import json
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

# ── Telemetry Streamer ─────────────────────────────────────────────────────────
from streamer import stream_telemetry

# ── Dashboard UI ──────────────────────────────────────────────────────────────
from ui.dashboard import render_sidebar, render_kpi_section, render_executive_summary
from ui.components import (
    kpi_card, status_indicator, action_card, agent_reasoning_panel,
    subscriber_card, alert_banner, live_log_display,
)
from ui.charts import (
    render_rsrp_chart, render_sinr_chart, render_ta_chart,
    render_prb_chart, render_handover_chart, render_congestion_heatmap,
)
from ui.maps import render_map_st
from config import DATA_DIR, STREAMLIT_PORT

# ── Global SSE State ───────────────────────────────────────────────────────────
_sse_loop: asyncio.AbstractEventLoop | None = None
_active_stream_task: asyncio.Task | None = None


# ── FastAPI App ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _sse_loop, _active_stream_task
    _sse_loop = asyncio.get_running_loop()
    yield
    # Cleanup
    if _active_stream_task:
        _active_stream_task.cancel()


app = FastAPI(
    title="CovMo Telecom Intelligence Platform",
    description="Intent-Based RAN Optimization · Urban Mobility Intelligence · AI Autonomous Operations",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "platform": "CovMo Telecom Intelligence Platform",
        "version": "1.0.0",
        "scenario": "Taipei Arena Power Station Concert Egress",
        "date": "May 15, 2026 22:00",
        "status": "operational",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "streamer_active": _active_stream_task is not None}


@app.get("/stream-trace")
async def stream_trace(request: Request):
    """
    Server-Sent Events endpoint for real-time telemetry streaming.

    Yields JSON payloads every 500ms containing:
    - telemetry: List[UETelemetry]
    - ran_alerts: List[RANAlert]
    - mobility: MobilityState
    - weather: WeatherState
    - reasoning: List[AgentReasoningEntry]
    - actions: List[AutonomousAction]
    - active_ues: int
    - tick: int
    """
    async def event_generator():
        try:
            async for payload in stream_telemetry():
                payload_str = json.dumps(payload, default=str)
                yield f"data: {payload_str}\n\n"
        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ── Streamlit Entry Point ──────────────────────────────────────────────────────
def run_streamlit():
    """Run Streamlit as a separate uvicorn app on port STREAMLIT_PORT."""
    from ui.dashboard import main as dashboard_main

    # Patch threading so Streamlit knows the main thread context
    import threading
    for t in threading.enumerate():
        add_script_run_ctx(t)

    # Run Streamlit on a different port via subprocess
    import subprocess
    import sys
    import os

    # Change to telecom_agent dir for relative paths
    app_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, app_dir)

    # Spawn Streamlit in a subprocess (the actual entry point)
    proc = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run",
        os.path.join(app_dir, "streamlit_app.py"),
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ])
    proc.wait()


# ── Unified main ───────────────────────────────────────────────────────────────
def main():
    """
    Unified entry point: starts FastAPI (SSE) + Streamlit together.
    Run with: streamlit run app.py
    """
    import threading
    import time

    # Start FastAPI in a background thread
    def run_api():
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    time.sleep(2)  # Let FastAPI start

    # Now start Streamlit
    import subprocess, sys, os
    app_dir = os.path.dirname(os.path.abspath(__file__))

    st_proc = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run",
        os.path.join(app_dir, "streamlit_app.py"),
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ])
    st_proc.wait()


# ── Standalone Streamlit App ───────────────────────────────────────────────────
# This file is imported by streamlit_app.py to provide the actual dashboard
# The dashboard is rendered here
def render_app():
    """Render the full dashboard."""
    from ui.dashboard import main
    main()


if __name__ == "__main__":
    main()
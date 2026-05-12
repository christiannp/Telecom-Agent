"""
ADK Runner for CovMo Telecom Intelligence Platform.

Run this AFTER starting fastapi_server.py and streamlit_app.py
to activate the multi-agent AI orchestration.

Usage:
    python adk_runner.py

This starts the ADK web interface on port 8080.
Open http://localhost:8080 to interact with the agents.
"""
from __future__ import annotations

import os, sys

# Ensure the project root is in the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from dotenv import load_dotenv

# Load .env from telecom_agent dir
_env_path = os.path.join(project_root, ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path, override=True)
else:
    # Try parent dir
    _env_path = os.path.join(os.path.dirname(project_root), ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path, override=True)

# ─────────────────────────────────────────────────────────────────────────────
# PROGRAMMATIC ADK AGENT INVOCATION
# Callable from the streaming pipeline to generate real AI reasoning.
# ─────────────────────────────────────────────────────────────────────────────

ADK_AVAILABLE = False
_runner = None
_root_agent = None


def _configure_logging():
    """Lazily configure litellm / uvicorn logging (only when ADK is used)."""
    try:
        import logging, litellm
        litellm._logging.loglevel = logging.DEBUG
        logging.getLogger("litellm").setLevel(logging.DEBUG)
        logging.getLogger("litellm.proxy").setLevel(logging.DEBUG)
        logging.getLogger("uvicorn.access").disabled = True
        logging.getLogger("uvicorn.error").disabled = False
        logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    except ImportError:
        pass


def _init_adk():
    """Lazily initialize ADK runtime (one-time, thread-safe)."""
    global ADK_AVAILABLE, _runner, _root_agent
    if ADK_AVAILABLE:
        return True
    try:
        _configure_logging()
        from google.adk.sessions import SessionService, InMemorySessionService
        from google.adk.runners import Runner
        from agents import root_agent
        _session_service = InMemorySessionService()
        _runner = Runner(
            agent=root_agent,
            app_name="covmo_telecom",
            session_service=_session_service,
        )
        _root_agent = root_agent
        ADK_AVAILABLE = True
        return True
    except ImportError:
        ADK_AVAILABLE = False
        return False


async def run_agent_analysis(
    tick: int,
    telemetry_context: dict,
    ran_alerts: list[dict],
    mobility_state: dict,
    weather_state: dict,
    correlated_events: list[dict] | None = None,
    limit: int = 6,
) -> dict | None:
    """
    Invoke the CovMo Intent Orchestration Agent with current system context.

    This is the bridge between the streaming pipeline and the ADK multi-agent
    system. It runs asynchronously so it does not block the telemetry stream.

    Returns a dict with keys: reasoning (str), confidence (float), color (str),
    triggered_action (str | None), agent_type (str), or None if ADK unavailable.

    Usage in streamer.py:
        agent_output = await run_agent_analysis(
            tick=_tick,
            telemetry_context=summary,
            ran_alerts=_ran_alerts,
            mobility_state=mobility.model_dump(),
            weather_state=weather.model_dump(),
            correlated_events=[e.model_dump() for e in correlated_events],
        )
    """
    if not _init_adk():
        return None

    # Build a compact context summary for the LLM prompt
    active_ues = telemetry_context.get("active_ues", 0)
    kpis = telemetry_context.get("kpis", {})

    alert_summary = (
        "None"
        if not ran_alerts
        else "; ".join(
            f"{a['alert_type']}({a['severity']})" for a in ran_alerts[:4]
        )
    )

    event_summary = (
        "None"
        if not correlated_events
        else "; ".join(
            f"{e.get('scenario_label', e.get('event_type','UNKNOWN'))}({e.get('severity','?')})"
            for e in correlated_events[:4]
        )
    )

    prompt = f"""CovMo Telecom — Streaming Analysis Request

CONCERT EGRESS SCENARIO | Tick {tick} | {active_ues} active UEs

CURRENT STATE:
- Tick: {tick} / ~150 UEs
- Subscriber Satisfaction: {kpis.get("subscriber_satisfaction_score", "?")} / 100
- VIP QoE Score: {kpis.get("vip_qoe_score", "?")} / 100
- Congestion Risk: {kpis.get("congestion_risk", "?")}%
- SLA Health: {kpis.get("sla_health", "?")}%
- Mobility Pressure: {kpis.get("predicted_mobility_pressure", "?")}%
- Mass Egress: {mobility_state.get("mass_egress_detected", False)}
- MRT Congestion: {mobility_state.get("overall_congestion", "?")}
- Egress Velocity: {mobility_state.get("egress_velocity_kmh", "?")} km/h
- Rainfall: {weather_state.get("rainfall_mm_hr", "?")} mm/hr
- Walking Propensity: {mobility_state.get("walking_propensity", "?")}%
- Slip Risk: {mobility_state.get("slip_risk", "?")}

ACTIVE ALERTS: {alert_summary}

CORRELATED SCENARIOS: {event_summary}

TASK: Provide a concise streaming analysis as the CovMo Intent Orchestration Agent.
Respond ONLY with this exact JSON (no markdown, no preamble):
{{
  "agent_type": "RAN|MOBILITY|CONTEXT|POLICY|INTENT",
  "color": "cyan|green|orange|red|purple",
  "confidence": 0-100,
  "reasoning": "One or two operational sentences with specific values.",
  "triggered_action": "action_type or null",
  "escalate_agent": "ran_intelligence|mobility_intelligence|context_intelligence|policy_validation|null"
}}
"""

    try:
        from google.adk.sessions import SessionService, InMemorySessionService
        from google.adk.runners import Runner
        import uuid as _uuid

        session_service = InMemorySessionService()
        runner = Runner(
            agent=_root_agent,
            app_name="covmo_telecom",
            session_service=session_service,
        )
        session = session_service.create_session(
            app_name="covmo_telecom",
            user_id="streamer",
            session_id=f"stream_{tick}_{uuid.uuid4().hex[:6]}",
        )

        response_stream = runner.run(
            user_id="streamer",
            session_id=session.id,
            new_message=prompt,
        )

        response_text = ""
        async for event in response_stream:
            if hasattr(event, "text") and event.text:
                response_text += event.text

        # Parse the JSON response
        import json as _json
        try:
            parsed = _json.loads(response_text.strip())
            return {
                "agent_type": parsed.get("agent_type", "INTENT"),
                "color": parsed.get("color", "cyan"),
                "confidence": float(parsed.get("confidence", 75.0)),
                "reasoning": parsed.get("reasoning", "Analysis in progress."),
                "triggered_action": parsed.get("triggered_action"),
                "escalate_agent": parsed.get("escalate_agent"),
            }
        except (_json.JSONDecodeError, Exception):
            # Fallback: return raw response
            return {
                "agent_type": "INTENT",
                "color": "cyan",
                "confidence": 75.0,
                "reasoning": response_text[:500] or "Streaming analysis active.",
                "triggered_action": None,
                "escalate_agent": None,
            }
    except Exception:
        return None


if __name__ == "__main__":
    import subprocess

    print("=" * 60)
    print("🤖 CovMo™ — ADK Multi-Agent Orchestration")
    print("=" * 60)
    print()
    print("Prerequisites:")
    print("  1. Start FastAPI SSE:  python fastapi_server.py")
    print("  2. Start Dashboard:    streamlit run streamlit_app.py")
    print()
    print("Starting ADK web server on http://localhost:8080")
    print()

    # Set up LiteLLM proxy in background
    lite_llm_proc = None
    try:
        print("[1/2] Starting LiteLLM proxy...")
        lite_llm_proc = subprocess.Popen(
            ["python", "-m", "litellm", "--config", "config.yaml"],
            cwd=project_root,
        )
    except Exception as e:
        print(f"  ⚠ LiteLLM proxy start skipped: {e}")

    # Give LiteLLM a moment to bind its port
    import time
    time.sleep(2)

    # Start ADK web
    print("[2/2] Starting ADK web server...")
    print()
    print("=" * 60)
    print("Once running, open your browser to:")
    print("  👉 http://localhost:8080")
    print()
    print("Agents available:")
    print("  📡 root_agent       — Intent Orchestration (coordinates all)")
    print("  📡 ran_intelligence — RAN analysis (signal cliffs, congestion)")
    print("  📡 mobility_intel   — Mobility analysis (MRT, YouBike)")
    print("  📡 context_intel    — Context analysis (weather, slip risk)")
    print("  📡 policy_validation— Policy governance (action approval)")
    print()
    print("Example queries:")
    print('  "Analyze the concert exit"')
    print('  "Show VIP congestion risk near Exit 2"')
    print('  "Predict MRT overload in 10 minutes"')
    print('  "Why did premium user QoE degrade?"')
    print("=" * 60)
    print()

    subprocess.run(
        ["python", "-m", "google.adk.cli.fast_api", "web",
         "--port", "8080",
         "--agent_path", project_root,
         "--allowed_origin", "*"],
        cwd=project_root,
    )

    # Cleanup
    if lite_llm_proc:
        lite_llm_proc.terminate()

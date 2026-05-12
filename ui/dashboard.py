"""
CovMo Telecom Intelligence Platform — Main Streamlit Dashboard.

Unified entry point: run with `streamlit run app.py`
"""
from __future__ import annotations

import json
import queue
import threading
import time
from pathlib import Path

import streamlit as st
import requests

from config import (
    STREAMLIT_PORT,
    TELEMETRY_INTERVAL_MS,
    UI_REFRESH_RATE,
    DATA_DIR,
    API_PORT,
    ADK_PORT,
    OLLAMA_API_KEY,
)
from services import set_replay_controller
from ui.components import (
    kpi_card,
    status_indicator,
    action_card,
    agent_reasoning_panel,
    subscriber_card,
    alert_banner,
    congestion_gauge,
    live_log_display,
    correlated_event_card,
    monitoring_escalation_panel,
    replay_controls,
    incident_arc_timeline,
)
from ui.charts import (
    render_rsrp_chart,
    render_sinr_chart,
    render_ta_chart,
    render_prb_chart,
    render_handover_chart,
    render_kpi_row,
    render_congestion_heatmap,
)
from ui.maps import render_map_st

DASHBOARD_CSS = """
<style>
    * { font-family: 'Courier New', monospace !important; }
    [data-testid="stAppViewContainer"] { background: #0A1428; }
    [data-testid="stHeader"] { background: #0A1428; border-bottom: 1px solid #1A2A3A; }
    [data-testid="stHorizontalBlock"] { padding: 0 4px; }
    .element-container { margin: 0 !important; }
    [data-testid="stMainBlockContainer"] { padding-top: 0.5rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { padding: 6px 14px; }
    section[data-testid="stSidebar"] { background: #0D1B2A; border-right: 1px solid #1A2A3A; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0A1428; }
    ::-webkit-scrollbar-thumb { background: #2A3A4A; border-radius: 3px; }
</style>
"""


# ── Page Setup ────────────────────────────────────────────────────────────────
def _configure_page() -> None:
    st.set_page_config(
        page_title="CovMo™ — Telecom Intelligence Platform",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────────────────────────
def _init_session_state() -> None:
    """Ensure Streamlit session keys exist even when this module is cached."""
    if "payload" not in st.session_state:
        st.session_state.payload = None
    if "history" not in st.session_state:
        st.session_state.history = []
    if "streaming" not in st.session_state:
        st.session_state.streaming = True
    if "auto_connect_initialized" not in st.session_state:
        st.session_state.auto_connect_initialized = True
        st.session_state.streaming = True
    if "log_lines" not in st.session_state:
        st.session_state.log_lines = []
    if "last_payload_received" not in st.session_state:
        st.session_state.last_payload_received = 0.0
    if "sse_error" not in st.session_state:
        st.session_state.sse_error = None

# ── SSE Polling Thread ─────────────────────────────────────────────────────────
# Queue used to safely bridge background thread → Streamlit main loop
_payload_queue: queue.Queue = queue.Queue(maxsize=1)
_sse_thread: threading.Thread | None = None
_sse_stop_event = threading.Event()
_sse_state_lock = threading.Lock()
_sse_state = {
    "connected": False,
    "error": None,
    "last_event_at": 0.0,
}


def _set_sse_state(**updates) -> None:
    with _sse_state_lock:
        _sse_state.update(updates)


def _get_sse_state() -> dict:
    with _sse_state_lock:
        return dict(_sse_state)


def _probe_json(url: str, timeout: float = 0.4):
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _api_is_ready() -> bool:
    data = _probe_json(f"http://127.0.0.1:{API_PORT}/health")
    return data == {"status": "healthy"}


def _adk_is_ready() -> bool:
    data = _probe_json(f"http://127.0.0.1:{ADK_PORT}/list-apps")
    return isinstance(data, list) and "telecom_agent" in data


def _start_sse_thread():
    """Poll the FastAPI SSE endpoint in a background thread, pushing updates
    into a bounded queue so the main loop can consume them without triggering
    the 'missing ScriptRunContext' warning."""
    global _sse_thread

    if _sse_thread and _sse_thread.is_alive():
        return

    _sse_stop_event.clear()
    _set_sse_state(connected=False, error=None)
    url = f"http://127.0.0.1:{API_PORT}/stream-trace"

    def poll():
        while not _sse_stop_event.is_set():
            try:
                with requests.get(url, stream=True, timeout=(3, 30)) as resp:
                    resp.raise_for_status()
                    _set_sse_state(connected=True, error=None)

                    for line in resp.iter_lines(decode_unicode=True):
                        if _sse_stop_event.is_set():
                            break
                        if not line or not line.startswith("data: "):
                            continue

                        data_str = line[6:]
                        try:
                            payload = json.loads(data_str)
                        except json.JSONDecodeError as exc:
                            _set_sse_state(error=f"Bad SSE payload: {exc}")
                            continue

                        if "error" in payload:
                            _set_sse_state(error=payload["error"])
                            continue

                        # Non-blocking put — drops stale payloads if the main loop is
                        # behind so the UI always shows the latest tick.
                        try:
                            _payload_queue.put_nowait(payload)
                        except queue.Full:
                            try:
                                _payload_queue.get_nowait()
                            except queue.Empty:
                                pass
                            _payload_queue.put_nowait(payload)

                        _set_sse_state(
                            connected=True,
                            error=None,
                            last_event_at=time.time(),
                        )
            except Exception as exc:
                _set_sse_state(connected=False, error=str(exc))
                if _sse_stop_event.wait(1.0):
                    break

        _set_sse_state(connected=False)

    _sse_thread = threading.Thread(target=poll, daemon=True)
    _sse_thread.start()


def _stop_sse_thread():
    _sse_stop_event.set()
    _set_sse_state(connected=False)


def _drain_queue():
    """Called every main-loop iteration to materialise queued payloads into
    session_state without triggering ScriptRunContext errors."""
    try:
        while True:
            payload = _payload_queue.get_nowait()
            st.session_state.payload = payload
            st.session_state.last_payload_received = time.time()
            st.session_state.sse_error = None

            hist = st.session_state.history
            hist.extend(payload.get("telemetry", []))
            if len(hist) > 200:
                hist[:] = hist[-200:]

            ts = payload.get("timestamp", "")[11:19]
            tick = payload.get("tick", 0)
            ues = payload.get("active_ues", 0)
            alerts = payload.get("ran_alerts", [])
            alert_str = f"[{alerts[0]['alert_type']}]" if alerts else "NOMINAL"
            line = f"TICK {tick:4d} | UEs {ues:3d} | {alert_str}"
            st.session_state.log_lines.append(line)
            if len(st.session_state.log_lines) > 100:
                st.session_state.log_lines[:] = st.session_state.log_lines[-100:]
    except queue.Empty:
        pass


def _schedule_refresh():
    """Keep the live dashboard moving without requiring manual clicks."""
    if not st.session_state.get("streaming"):
        return

    refresh_interval = max(0.25, float(UI_REFRESH_RATE))
    time.sleep(refresh_interval)
    st.rerun()


# ── Load cell data ────────────────────────────────────────────────────────────
def _load_cells() -> list:
    path = DATA_DIR / "mock_cells.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


# ── Sidebar: System Status ─────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 📡 CovMo™ Platform")
        st.markdown("**Taipei Arena Concert Egress**\n*Power Station — May 15, 2026*")
        st.divider()

        st.markdown("### 🔌 System Status")

        payload = st.session_state.get("payload")
        api_ready = _api_is_ready()
        adk_ready = _adk_is_ready()
        sse_state = _get_sse_state()
        payload_age = time.time() - st.session_state.last_payload_received
        sse_live = bool(payload) and payload_age < max(3.0, float(UI_REFRESH_RATE) * 3)

        status_indicator(
            "Ollama LLM",
            "CONFIGURED" if OLLAMA_API_KEY else "MISSING KEY",
            "green" if OLLAMA_API_KEY else "red",
        )
        status_indicator(
            "SSE Streamer",
            "ACTIVE" if sse_live else "READY" if api_ready else "OFFLINE",
            "cyan" if api_ready else "red",
        )
        status_indicator(
            "AI Orchestration",
            "RUNNING" if sse_live else "READY" if adk_ready else "ADK OFFLINE",
            "purple" if adk_ready else "red",
        )
        status_indicator(
            "SSE Connection",
            "LIVE" if sse_live else "CONNECTING" if st.session_state.streaming and api_ready else "OFFLINE",
            "green" if sse_live else "orange" if st.session_state.streaming and api_ready else "red",
        )

        if sse_state.get("error") and not sse_live:
            st.caption(f"SSE: {sse_state['error']}")

        if payload:
            status_indicator("Active Agents", "5 AGENTS", "cyan")

            tick = payload.get("tick", 0)
            ues = payload.get("active_ues", 0)
            rate = (ues * 2) if ues else 0
            status_indicator(f"Event Throughput", f"{rate} eps", "cyan")
            status_indicator("Telemetry Ingestion", f"{tick} ticks", "cyan")
            status_indicator("Tick Counter", f"#{tick}", "green")

            st.divider()

            # Mobility summary
            mob = payload.get("mobility", {})
            if mob:
                st.markdown("### 🚇 MRT Status")
                congestion = mob.get("overall_congestion", "GREEN")
                color = "green" if congestion == "GREEN" else "orange" if congestion == "YELLOW" else "red"
                status_indicator("MRT Congestion", congestion, color)
                status_indicator("Mass Egress", "DETECTED" if mob.get("mass_egress_detected") else "STANDBY", "orange")
                status_indicator("Walk Propensity", f"{mob.get('walking_propensity', 1.0)*100:.0f}%", "cyan")
                status_indicator("Slip Risk", mob.get("slip_risk", "LOW"), "orange")

                # YouBike
                st.markdown("### 🚲 YouBike")
                status_indicator("Available", f"{mob.get('youbike_available', 0)} bikes", "green")
                status_indicator("Empty Docks", f"{mob.get('youbike_empty_docks', 0)} docks", "orange")

        st.divider()

        # Start/Stop controls
        if st.session_state.streaming:
            if st.button("■ Stop Streaming", use_container_width=True):
                st.session_state.streaming = False
                _stop_sse_thread()
                st.rerun()
            if st.button("↻ Reconnect SSE", use_container_width=True):
                _stop_sse_thread()
                time.sleep(0.2)
                _start_sse_thread()
                st.rerun()
        else:
            if st.button("▶ Start Streaming", type="primary", use_container_width=True):
                st.session_state.streaming = True
                _start_sse_thread()
                st.rerun()

        st.caption("CovMo™ GenAI Telecom Intelligence Platform v1.0")


# ── KPI Section ───────────────────────────────────────────────────────────────
def render_kpi_section(kpis: dict):
    # Use the kpis argument directly — don't reassign from payload
    cols = st.columns(7)
    metrics = [
        ("Subscriber Satisfaction", kpis.get("subscriber_satisfaction_score", 0), "cyan"),
        ("VIP QoE Score", kpis.get("vip_qoe_score", 0), "orange"),
        ("Congestion Risk", kpis.get("congestion_risk", 0), "red"),
        ("AI Confidence", kpis.get("ai_confidence", 0), "purple"),
        ("SLA Health", kpis.get("sla_health", 0), "green"),
        ("Revenue Protection", f"${kpis.get('revenue_protection_usd', 0):.0f}", "cyan"),
        ("Mobility Pressure", kpis.get("predicted_mobility_pressure", 0), "orange"),
    ]
    for col, (title, val, color) in zip(cols, metrics):
        with col:
            if isinstance(val, float):
                kpi_card(title, f"{val:.1f}", color=color)
            else:
                kpi_card(title, str(val), color=color)


# ── Executive Summary ────────────────────────────────────────────────────────
def render_executive_summary(kpis: dict):
    with st.expander("📊 Executive Summary", expanded=True):
        cols = st.columns(5)
        summary_items = [
            ("Congestion Prevented", f"{kpis.get('congestion_prevented', 0):.1f}%", "green"),
            ("Est SLA Savings", f"${kpis.get('estimated_sla_savings_usd', 0):.0f}", "orange"),
            ("AI Mitigation Success", f"{kpis.get('ai_mitigation_success_rate', 0):.1f}%", "grey"),
            ("VIP Retention Risk Reduction", f"{kpis.get('vip_retention_risk_reduction', 0):.1f}%", "purple"),
            ("Active UEs", f"{st.session_state.payload.get('active_ues', 0) if st.session_state.payload else 0}", "cyan"),
        ]
        for col, (title, val, color) in zip(cols, summary_items):
            with col:
                kpi_card(title, val, color=color)
    
    # Fix st.expander _arrow_ issue due to newer Streamlit versions
    st.markdown("""
    <style>
    [data-testid="stIconMaterial"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ── Main Layout ───────────────────────────────────────────────────────────────
def main():
    _configure_page()
    _init_session_state()

    if st.session_state.streaming:
        _start_sse_thread()

    # Drain SSE payloads from background thread into session_state
    _drain_queue()

    render_sidebar()

    st.markdown("""
    <div style="padding: 8px 16px; background: #0D1B2A; border-bottom: 1px solid #1A2A3A; margin-bottom: 8px;">
        <span style="color:#00E5FF; font-size:18px; font-weight:700; font-family:'Courier New',monospace;">
            📡 COVMO™ TELECOM INTELLIGENCE PLATFORM
        </span>
        <span style="color:#B0BEC5; font-size:12px; margin-left:20px; font-family:'Courier New',monospace;">
            Intent-Based RAN Optimization · Urban Mobility Intelligence · AI Autonomous Operations
        </span>
    </div>
    """, unsafe_allow_html=True)

    payload = st.session_state.payload

    if not payload:
        st.markdown("""
        <div style="text-align:center; padding: 80px 20px; color:#B0BEC5; font-family:'Courier New',monospace;">
            <div style="font-size:48px; margin-bottom:20px;">📡</div>
            <div style="font-size:24px; color:#00E5FF; margin-bottom:10px;">CovMo™ Platform Connecting</div>
            <div style="font-size:14px;">Waiting for the first SSE telemetry frame...</div>
        </div>
        """, unsafe_allow_html=True)
        _schedule_refresh()
        return

    kpis = payload.get("telemetry", [{}])
    # Get KPIs from telemetry service
    from services.telemetry_service import get_kpi_snapshot
    kpis = get_kpi_snapshot().model_dump()
    del kpis["timestamp"]

    # KPI Panel
    render_kpi_section(kpis)

    # Executive Summary
    render_executive_summary(kpis)

    st.divider()

    # ── Main Grid ─────────────────────────────────────────────────────────────
    tab_names = ["📊 Operational", "🗺️ Mobility Map", "🤖 AI Console", "📡 Subscribers"]
    tab_ops, tab_map, tab_ai, tab_sub = st.tabs(tab_names)

    history = st.session_state.history

    with tab_ops:
        # Row 1: RSRP + SINR charts
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.plotly_chart(render_rsrp_chart(history[-80:]), use_container_width=True)
        with col_chart2:
            st.plotly_chart(render_sinr_chart(history[-80:]), use_container_width=True)

        # Row 2: TA + PRB
        col_chart3, col_chart4 = st.columns(2)
        with col_chart3:
            st.plotly_chart(render_ta_chart(history[-80:]), use_container_width=True)
        with col_chart4:
            st.plotly_chart(render_prb_chart(history[-80:]), use_container_width=True)

        # Row 3: Handover + Heatmap
        col_chart5, col_chart6 = st.columns(2)
        with col_chart5:
            st.plotly_chart(render_handover_chart(history[-80:]), use_container_width=True)
        with col_chart6:
            st.plotly_chart(render_congestion_heatmap(history[-60:]), use_container_width=True)

    with tab_map:
        cells = _load_cells()
        egress_progress = min(1.0, (payload.get("tick", 0) * 0.006))
        exit_data = payload.get("mobility", {}).get("mrt_exits", [])
        telemetry = payload.get("telemetry", [])
        render_map_st(telemetry, cells, egress_progress)

        # Legend
        st.markdown("""
        <div style="display:flex; gap:20px; font-family:'Courier New',monospace; font-size:11px; color:#B0BEC5; padding: 8px 0;">
            <span>🔴 <b>RED</b> = Poor RSRP (<-105dBm)</span>
            <span>🟠 <b>ORANGE</b> = Fair RSRP (-90 to -105dBm)</span>
            <span>🟢 <b>GREEN</b> = Good RSRP (>-90dBm)</span>
            <span>★ <b>VIP</b> subscribers shown larger</span>
        </div>
        """, unsafe_allow_html=True)

    with tab_ai:
        # ── Incident Arc Timeline ─────────────────────────────────────────────
        arcs = payload.get("incident_arcs", {})
        if arcs:
            st.markdown("### 🎭 Active Incident Arcs")
            incident_arc_timeline(arcs)
            st.divider()

        # ── Correlated Events ─────────────────────────────────────────────────
        st.markdown("### 🔗 Event Correlation Engine")
        correlated = payload.get("correlated_events", [])
        if not correlated:
            st.info("No correlated scenarios detected yet — analyzing cross-domain signals...")
        else:
            cols = st.columns(2)
            for i, evt in enumerate(correlated[:6]):
                with cols[i % 2]:
                    correlated_event_card(evt)
        st.divider()

        # ── Continuous Monitoring ─────────────────────────────────────────────
        st.markdown("### 🔄 Agent Monitoring Escalation")
        escalations = payload.get("monitoring_escalations", {})
        monitoring_escalation_panel(escalations)
        st.divider()

        # ── AI Reasoning Console ───────────────────────────────────────────────
        st.markdown("### 🤖 Multi-Agent Reasoning Console")
        reasoning = payload.get("reasoning", [])
        agent_reasoning_panel(reasoning)
        st.divider()

        # ── Autonomous Actions ─────────────────────────────────────────────────
        st.markdown("### ⚡ Autonomous AI Actions (Policy-Validated)")
        actions = payload.get("actions", [])
        if not actions:
            st.info("No autonomous actions triggered yet. AI is monitoring...")
        else:
            approved = [a for a in actions if a.get("status") in ("approved", "executed")]
            rejected = [a for a in actions if a.get("status") == "rejected"]

            if approved:
                st.markdown(f"**Approved & Executed ({len(approved)})**")
                for act in approved:
                    action_card(
                        action_type=act.get("action_type", "UNKNOWN"),
                        severity="GREEN",
                        confidence=act.get("confidence_score", 0),
                        reason=act.get("reason", ""),
                        impact=act.get("expected_kpi_improvement_pct", 0),
                        policy_approved=True,
                        status="executed",
                    )

            if rejected:
                st.markdown(f"**Rejected by Policy Engine ({len(rejected)})**")
                for act in rejected:
                    action_card(
                        action_type=act.get("action_type", "UNKNOWN"),
                        severity="RED",
                        confidence=act.get("confidence_score", 0),
                        reason=act.get("policy_reject_reason", act.get("reason", "")),
                        impact=act.get("expected_kpi_improvement_pct", 0),
                        policy_approved=False,
                        status="rejected",
                    )

        st.divider()

        # ── Incident Replay ───────────────────────────────────────────────────
        st.markdown("### 🎬 Incident Replay")
        replay_controls()

    with tab_sub:
        st.markdown("### 📡 VIP Subscriber Analytics")
        vips = payload.get("telemetry", [])
        vip_telemetry = [t for t in vips if t.get("qos_class") == "VIP_Premium"]

        if vip_telemetry:
            # Show top 6 VIP subscribers
            cols = st.columns(3)
            for i, vip in enumerate(vip_telemetry[:6]):
                sub_data = {
                    "ue_id": vip.get("ue_id", "N/A"),
                    "qos_class": vip.get("qos_class", "VIP_Premium"),
                    "is_vip": True,
                    "frustration_index": max(0, 100 + vip.get("metrics", {}).get("rsrp", -100)),
                    "handover_count": 0 if vip.get("metrics", {}).get("handover_success", True) else 1,
                    "qoe_degradation_predicted_min": 4.0,
                }
                with cols[i % 3]:
                    subscriber_card(sub_data)
        else:
            st.info("Waiting for VIP subscriber telemetry...")

        # RAN Alerts
        st.markdown("### 🚨 Active RAN Alerts")
        alerts = payload.get("ran_alerts", [])
        if not alerts:
            st.success("✓ No active RAN alerts — all systems nominal")
        for alert in alerts:
            alert_banner(alert)

        # Live Log
        st.markdown("### 📋 Live Telemetry Log")
        live_log_display(st.session_state.log_lines)

    _schedule_refresh()


if __name__.startswith("streamlit"):
    main()

"""
CovMo Telecom Intelligence Platform — Main Streamlit Dashboard.

Unified entry point: run with `streamlit run app.py`
"""
from __future__ import annotations

import json
import asyncio
import threading
import time
from pathlib import Path

import streamlit as st
import requests

from config import STREAMLIT_PORT, TELEMETRY_INTERVAL_MS, DATA_DIR
from ui.components import (
    kpi_card,
    status_indicator,
    action_card,
    agent_reasoning_panel,
    subscriber_card,
    alert_banner,
    congestion_gauge,
    live_log_display,
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

# ── Dark Theme CSS ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CovMo™ — Telecom Intelligence Platform",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown("""
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
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────────────────────────
if "payload" not in st.session_state:
    st.session_state.payload = None
if "history" not in st.session_state:
    st.session_state.history = []
if "streaming" not in st.session_state:
    st.session_state.streaming = False
if "log_lines" not in st.session_state:
    st.session_state.log_lines = []


# ── SSE Polling Thread ─────────────────────────────────────────────────────────
def _start_sse_thread():
    """Poll the FastAPI SSE endpoint in a background thread."""
    url = "http://localhost:8000/stream-trace"

    def poll():
        try:
            resp = requests.get(url, stream=True, timeout=30)
            for line in resp.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        payload = json.loads(data_str)
                        if st.session_state:
                            st.session_state.payload = payload

                            # Build history
                            hist = st.session_state.history
                            hist.extend(payload.get("telemetry", []))
                            if len(hist) > 200:
                                hist[:] = hist[-200:]
                            st.session_state.history = hist

                            # Log line
                            ts = payload.get("timestamp", "")[11:19]
                            tick = payload.get("tick", 0)
                            ues = payload.get("active_ues", 0)
                            alerts = payload.get("ran_alerts", [])
                            alert_str = f"[{alerts[0]['alert_type']}]" if alerts else "NOMINAL"
                            line = f"TICK {tick:4d} | UEs {ues:3d} | {alert_str}"
                            st.session_state.log_lines.append(line)
                            if len(st.session_state.log_lines) > 100:
                                st.session_state.log_lines[:] = st.session_state.log_lines[-100:]
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

    t = threading.Thread(target=poll, daemon=True)
    t.start()


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
        if payload:
            status_indicator("Ollama LLM", "CONNECTED", "green")
            status_indicator("SSE Streamer", "ACTIVE", "cyan")
            status_indicator("AI Orchestration", "RUNNING", "purple")
            status_indicator("SSE Connection", "LIVE", "green")
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

        else:
            status_indicator("Ollama LLM", "CONNECTING...", "orange")
            status_indicator("SSE Streamer", "STANDBY", "grey")
            status_indicator("AI Orchestration", "IDLE", "grey")
            status_indicator("SSE Connection", "OFFLINE", "red")

        st.divider()

        # Start/Stop controls
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
            ("Est. SLA Savings", f"${kpis.get('estimated_sla_savings_usd', 0):.0f}", "cyan"),
            ("AI Mitigation Success", f"{kpis.get('ai_mitigation_success_rate', 0):.1f}%", "green"),
            ("VIP Retention Risk Reduction", f"{kpis.get('vip_retention_risk_reduction', 0):.1f}%", "purple"),
            ("Active UEs", f"{st.session_state.payload.get('active_ues', 0) if st.session_state.payload else 0}", "cyan"),
        ]
        for col, (title, val, color) in zip(cols, summary_items):
            with col:
                kpi_card(title, val, color=color)


# ── Main Layout ───────────────────────────────────────────────────────────────
def main():
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
            <div style="font-size:24px; color:#00E5FF; margin-bottom:10px;">CovMo™ Platform Initializing</div>
            <div style="font-size:14px;">Streaming synthetic telecom telemetry...</div>
            <div style="font-size:14px; margin-top:8px;">Click <b>▶ Start Streaming</b> in the sidebar to begin.</div>
        </div>
        """, unsafe_allow_html=True)
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
        # AI Reasoning Console
        st.markdown("### 🤖 Multi-Agent Reasoning Console")
        reasoning = payload.get("reasoning", [])
        agent_reasoning_panel(reasoning)

        st.divider()

        # Autonomous Actions
        st.markdown("### ⚡ Autonomous AI Actions")
        actions = payload.get("actions", [])
        if not actions:
            st.info("No autonomous actions triggered yet. AI is monitoring...")
        for act in actions:
            severity = "GREEN"
            if act.get("expected_kpi_improvement_pct", 0) > 15:
                severity = "ORANGE"
            if act.get("status") == "REJECTED":
                severity = "RED"
            action_card(
                action_type=act.get("action_type", "UNKNOWN"),
                severity=severity,
                confidence=act.get("confidence_score", 0),
                reason=act.get("reason", ""),
                impact=act.get("expected_kpi_improvement_pct", 0),
                policy_approved=act.get("policy_approved", False),
                status=act.get("status", "proposed"),
            )

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


if __name__.startswith("streamlit"):
    main()
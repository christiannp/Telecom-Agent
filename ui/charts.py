"""Plotly chart renderers for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

from typing import List, Dict, Any

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


# ── Color Palette ─────────────────────────────────────────────────────────────
DARK_BG = "#0A1428"
DARK_PANEL = "#0D1B2A"
CARD_BG = "#1A2A3A"
CYAN = "#00E5FF"
GREEN = "#00E676"
ORANGE = "#FF9100"
RED = "#FF1744"
PURPLE = "#E040FB"
GREY = "#B0BEC5"
ACCENT = "#00BFFF"


def _base_layout(fig: go.Figure, title: str, height: int = 280) -> go.Figure:
    """Apply dark theme layout to a Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_PANEL,
        font=dict(color=GREY, family="Courier New, monospace"),
        title=dict(text=title, font=dict(color=CYAN, size=14), x=0.5),
        margin=dict(l=40, r=20, t=40, b=40),
        height=height,
        xaxis=dict(
            showgrid=True, gridcolor="#1A2A3A",
            zeroline=False, showline=False,
            color=GREY, title_font=dict(color=GREY), tickfont=dict(color=GREY, size=10)
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#1A2A3A",
            zeroline=False, showline=False,
            color=GREY, title_font=dict(color=GREY), tickfont=dict(color=GREY, size=10)
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", font=dict(color=GREY),
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )
    return fig


# ── RSRP Trend Chart ───────────────────────────────────────────────────────────
def render_rsrp_chart(telemetry_history: List[Dict]) -> go.Figure:
    """RSRP over time with VIP highlight."""
    if not telemetry_history:
        return _empty_chart("RSRP Trend — No Data")

    # Build per-UE time series
    vip_data = {}
    std_data = {}

    for i, t in enumerate(telemetry_history):
        uid = t.get("ue_id", "?")
        rsrp = t.get("metrics", {}).get("rsrp")
        if rsrp is None:
            continue
        is_vip = t.get("qos_class") == "VIP_Premium"
        target = vip_data if is_vip else std_data
        target.setdefault("x", []).append(i)
        target.setdefault("y", []).append(rsrp)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.08, row_heights=[0.6, 0.4])
    fig._subplots_takes_config = None  # reset

    if std_data:
        fig.add_trace(go.Scatter(
            x=std_data["x"], y=std_data["y"],
            mode="lines", name="Standard",
            line=dict(color=GREY, width=1), opacity=0.5,
            hovertemplate="Tick %{x}<br>RSRP: %{y:.1f} dBm<extra>Standard</extra>"
        ), row=1, col=1)

    if vip_data:
        fig.add_trace(go.Scatter(
            x=vip_data["x"], y=vip_data["y"],
            mode="lines", name="VIP",
            line=dict(color=RED, width=2),
            hovertemplate="Tick %{x}<br>RSRP: %{y:.1f} dBm<extra>VIP</extra>"
        ), row=1, col=1)

    # Add threshold lines
    for row_y, threshold, label, color in [
        (-90, -90, "Good threshold", GREEN),
        (-105, -105, "Poor threshold", ORANGE),
    ]:
        fig.add_hline(y=threshold, line_dash="dash", line_color=color,
                      opacity=0.6, annotation_text=label, row="all", col=1)

    fig.update_layout(
        template="plotly_dark", paper_bgcolor=DARK_BG, plot_bgcolor=DARK_PANEL,
        font=dict(color=GREY, family="Courier New, monospace"),
        title=dict(text="📶 RSRP Trend (dBm)", font=dict(color=CYAN, size=13), x=0.5),
        height=280, margin=dict(l=45, r=20, t=45, b=30),
        xaxis=dict(showgrid=True, gridcolor="#1A2A3A", color=GREY, tickfont=dict(color=GREY, size=9)),
        xaxis2=dict(showgrid=True, gridcolor="#1A2A3A", color=GREY, tickfont=dict(color=GREY, size=9),
                    title="Telemetry Tick"),
        yaxis=dict(showgrid=True, gridcolor="#1A2A3A", color=GREY, tickfont=dict(color=GREY, size=9),
                   title="RSRP (dBm)"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=GREY), orientation="h",
                    yanchor="bottom", y=1.12, xanchor="right", x=1),
    )
    return fig


# ── SINR Trend Chart ───────────────────────────────────────────────────────────
def render_sinr_chart(telemetry_history: List[Dict]) -> go.Figure:
    """SINR over time."""
    if not telemetry_history:
        return _empty_chart("SINR Trend — No Data")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(telemetry_history))),
        y=[t.get("metrics", {}).get("sinr", 0) for t in telemetry_history],
        mode="lines", name="SINR",
        line=dict(color=ACCENT, width=2),
        fill="tozeroy", fillcolor="rgba(0,191,255,0.08)",
        hovertemplate="Tick %{x}<br>SINR: %{y:.1f} dB<extra></extra>"
    ))
    fig.add_hline(y=15, line_dash="dash", line_color=GREEN, opacity=0.6,
                  annotation_text="Good (>15dB)")
    fig.add_hline(y=8, line_dash="dash", line_color=ORANGE, opacity=0.6,
                  annotation_text="Poor (<8dB)")

    return _base_layout(fig, "📡 SINR Trend (dB)", height=220)


# ── TA Trend Chart ─────────────────────────────────────────────────────────────
def render_ta_chart(telemetry_history: List[Dict]) -> go.Figure:
    """Timing Advance (TA) over time — indicates crowd movement toward MRT."""
    if not telemetry_history:
        return _empty_chart("TA Trend — No Data")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(telemetry_history))),
        y=[t.get("metrics", {}).get("ta", 0) for t in telemetry_history],
        mode="lines+markers", name="TA",
        line=dict(color=PURPLE, width=2),
        marker=dict(size=3, color=PURPLE),
        fill="tozeroy", fillcolor="rgba(224,64,251,0.08)",
        hovertemplate="Tick %{x}<br>TA: %{y}<extra></extra>"
    ))

    # Mass egress line
    fig.add_hline(y=30, line_dash="dot", line_color=ORANGE, opacity=0.7,
                  annotation_text="MRT ingress zone")
    return _base_layout(fig, "⏱ Timing Advance — Distance from Cell (TA×78m)", height=220)


# ── PRB Utilization Chart ─────────────────────────────────────────────────────
def render_prb_chart(telemetry_history: List[Dict]) -> go.Figure:
    """PRB (Physical Resource Block) utilization — congestion indicator."""
    if not telemetry_history:
        return _empty_chart("PRB Utilization — No Data")

    prb_vals = [t.get("metrics", {}).get("prb_utilization", 0) for t in telemetry_history]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(prb_vals))),
        y=prb_vals,
        mode="lines", name="PRB %",
        line=dict(color=ORANGE, width=2),
        fill="tozeroy", fillcolor="rgba(255,145,0,0.12)",
        hovertemplate="Tick %{x}<br>PRB: %{y:.1f}%<extra></extra>"
    ))
    fig.add_hline(y=80, line_dash="dash", line_color=RED, opacity=0.7,
                  annotation_text="Congestion threshold")
    fig.add_hline(y=60, line_dash="dash", line_color=ORANGE, opacity=0.4,
                  annotation_text="Warning")

    return _base_layout(fig, "📊 PRB Utilization (%)", height=220)


# ── Handover Success Rate ──────────────────────────────────────────────────────
def render_handover_chart(telemetry_history: List[Dict]) -> go.Figure:
    """Handover success rate over time."""
    if not telemetry_history:
        return _empty_chart("Handover Success Rate — No Data")

    window = min(20, len(telemetry_history))
    success_rates = []
    for i in range(len(telemetry_history)):
        window_data = telemetry_history[max(0, i-window+1):i+1]
        total = len(window_data)
        successes = sum(1 for t in window_data if t.get("metrics", {}).get("handover_success", True))
        success_rates.append((successes / total * 100) if total > 0 else 100)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(success_rates))),
        y=success_rates,
        mode="lines", name="Success Rate",
        line=dict(color=GREEN, width=2),
        fill="tozeroy", fillcolor="rgba(0,230,118,0.1)",
        hovertemplate="Tick %{x}<br>Success: %{y:.0f}%<extra></extra>"
    ))
    fig.add_hline(y=95, line_dash="dash", line_color=GREEN, opacity=0.5,
                  annotation_text="95% target")
    fig.update_yaxes(range=[80, 101])
    return _base_layout(fig, "🔄 Handover Success Rate (%)", height=220)


# ── KPI Gauge ─────────────────────────────────────────────────────────────────
def render_kpi_gauge(value: float, label: str, unit: str = "%",
                      color: str | None = None) -> go.Figure:
    """Single KPI gauge chart."""
    if color is None:
        color = GREEN if value > 70 else ORANGE if value > 40 else RED

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": unit, "font": {"color": color, "size": 28, "family": "Courier New"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": GREY, "tickfont": {"color": GREY}},
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": CARD_BG,
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "#1A0000"},
                {"range": [50, 80], "color": "#1A1500"},
                {"range": [80, 100], "color": "#001A00"},
            ],
        },
        title={"text": label, "font": {"color": GREY, "size": 11, "family": "Courier New"}},
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
        margin=dict(l=10, r=10, t=40, b=10), height=130,
    )
    return fig


# ── KPI Row Gauges ────────────────────────────────────────────────────────────
def render_kpi_row(kpis: Dict) -> go.Figure:
    """Render a row of 4 KPI gauges."""
    metrics = [
        ("Subscriber Satisfaction", kpis.get("subscriber_satisfaction_score", 0), "%"),
        ("VIP QoE Score", kpis.get("vip_qoe_score", 0), "%"),
        ("SLA Health", kpis.get("sla_health", 0), "%"),
        ("AI Confidence", kpis.get("ai_confidence", 0), "%"),
    ]

    fig = make_subplots(
        rows=1, cols=4,
        specs=[[{"type": "indicator"}]*4],
        horizontal_spacing=0.05,
    )
    colors = [GREEN, CYAN, GREEN, PURPLE]
    for col, (label, val, unit) in enumerate(metrics, 1):
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=round(val, 1),
            number={"suffix": unit, "font": {"color": colors[col-1], "size": 20,
                                               "family": "Courier New"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": GREY, "tickfont": {"color": GREY, "size": 8}},
                "bar": {"color": colors[col-1], "thickness": 0.25},
                "bgcolor": CARD_BG, "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "#1A0000"},
                    {"range": [50, 80], "color": "#1A1500"},
                    {"range": [80, 100], "color": "#001500"},
                ],
            },
            title={"text": label, "font": {"color": GREY, "size": 9, "family": "Courier New"}},
        ), row=1, col=col)

    fig.update_layout(
        template="plotly_dark", paper_bgcolor=DARK_BG,
        font=dict(family="Courier New"),
        margin=dict(l=5, r=5, t=30, b=5), height=140,
    )
    return fig


# ── Utility ───────────────────────────────────────────────────────────────────
def _empty_chart(title: str) -> go.Figure:
    """Return an empty placeholder chart."""
    fig = go.Figure()
    fig.add_annotation(text=title + "\n[Waiting for data...]",
                      xref="paper", yref="paper",
                      x=0.5, y=0.5, showarrow=False,
                      font=dict(color=GREY, size=14, family="Courier New"))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=DARK_BG, plot_bgcolor=DARK_PANEL,
        height=200, margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


def render_congestion_heatmap(telemetry_history: List[Dict]) -> go.Figure:
    """Heatmap of PRB utilization vs congestion over time."""
    if not telemetry_history:
        return _empty_chart("Congestion Heatmap — No Data")

    # Aggregate PRB by time window
    window = max(1, len(telemetry_history) // 20)
    prb_matrix = []
    for i in range(0, len(telemetry_history), window):
        chunk = telemetry_history[i:i+window]
        prb_vals = [t.get("metrics", {}).get("prb_utilization", 0) for t in chunk]
        prb_matrix.append(prb_vals)

    fig = go.Figure(data=go.Heatmap(
        z=prb_matrix,
        colorscale=[[0, "#001500"], [0.5, "#FF9100"], [1, "#FF1744"]],
        showscale=True,
        colorbar=dict(title="PRB %", tickfont=dict(color=GREY, size=9),
                      title_font=dict(color=GREY)),
        hovertemplate="Window %{x}<br>UE %{y}<br>PRB: %{z:.1f}%<extra></extra>"
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=DARK_BG, plot_bgcolor=DARK_PANEL,
        font=dict(color=GREY, family="Courier New"),
        title=dict(text="🔥 Congestion Heatmap", font=dict(color=ORANGE, size=13), x=0.5),
        height=200, margin=dict(l=40, r=20, t=40, b=30),
        xaxis=dict(title="Time Window", color=GREY, showgrid=False, tickfont=dict(color=GREY, size=9)),
        yaxis=dict(title="UE Index", color=GREY, showgrid=False, tickfont=dict(color=GREY, size=9)),
    )
    return fig
"""Reusable Streamlit UI components for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


# ── Color Palette ─────────────────────────────────────────────────────────────
COLORS = {
    "navy": "#0D1B2A",
    "dark_navy": "#0A1428",
    "cyan": "#00E5FF",
    "green": "#00E676",
    "orange": "#FF9100",
    "red": "#FF1744",
    "purple": "#E040FB",
    "yellow": "#FFEA00",
    "grey": "#B0BEC5",
    "dark_card": "#1A2A3A",
    "border": "#2A3A4A",
}


# ── KPI Card ─────────────────────────────────────────────────────────────────
def kpi_card(title: str, value: str | float, delta: str | None = None,
             color: str = "cyan", width: int = 200) -> None:
    """Render a premium KPI metric card with optional delta."""
    color_hex = COLORS.get(color, COLORS["cyan"])
    delta_html = ""
    if delta is not None:
        delta_color = COLORS["green"] if "+" in str(delta) else COLORS["red"]
        delta_html = f'<span style="color:{delta_color}; font-size:13px; margin-left:8px;">{delta}</span>'

    html = f"""
    <style>
    @keyframes kpi-pulse-{title.replace(' ', '-')} {{
        0% {{ opacity: 0.8; }}
        50% {{ opacity: 1; }}
        100% {{ opacity: 0.8; }}
    }}
    .kpi-card-{title.replace(' ', '-')} {{
        background: linear-gradient(135deg, #0D1B2A 0%, #1A2A3A 100%);
        border: 1px solid {color_hex}40;
        border-left: 3px solid {color_hex};
        border-radius: 8px;
        padding: 16px 20px;
        margin: 4px 0;
        animation: kpi-pulse-{title.replace(' ', '-')} 3s infinite;
    }}
    .kpi-title {{
        color: {COLORS['grey']};
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-family: 'Courier New', monospace;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        color: {color_hex};
        font-size: 28px;
        font-weight: 700;
        font-family: 'Courier New', monospace;
        display: flex;
        align-items: center;
    }}
    </style>
    <div class="kpi-card-{title.replace(' ', '-')}">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}{delta_html}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Status Indicator ──────────────────────────────────────────────────────────
def status_indicator(label: str, status: str, color: str | None = None) -> None:
    """Render a status badge (OK / WARNING / CRITICAL)."""
    status_lower = status.upper()
    status_upper = status_lower
    if color is None:
        if "OK" in status_upper:
            color = COLORS["green"]
        elif "WARN" in status_upper or "YELLOW" in status_upper:
            color = COLORS["orange"]
        elif "CRIT" in status_upper or "RED" in status_upper:
            color = COLORS["red"]
        elif "PURPLE" in status_upper:
            color = COLORS["purple"]
        else:
            color = COLORS["cyan"]

    dot_color = color
    bg_color = color + "20"

    html = f"""
    <style>
    .status-item-{label.replace(' ', '-')} {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 0;
        font-family: 'Courier New', monospace;
        font-size: 12px;
    }}
    .status-dot {{
        width: 8px; height: 8px;
        border-radius: 50%;
        background: {dot_color};
        box-shadow: 0 0 6px {dot_color};
        animation: status-blink 2s infinite;
    }}
    @keyframes status-blink {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.4; }}
    }}
    .status-label {{ color: {COLORS['grey']}; }}
    .status-value {{ color: {color}; font-weight: 600; }}
    </style>
    <div class="status-item-{label.replace(' ', '-')}">
        <div class="status-dot"></div>
        <span class="status-label">{label}:</span>
        <span class="status-value">{status}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Action Card ──────────────────────────────────────────────────────────────
def action_card(
    action_type: str,
    severity: str,
    confidence: float,
    reason: str,
    impact: float,
    policy_approved: bool = True,
    status: str = "proposed",
) -> None:
    """Render an autonomous AI action card with severity color coding."""
    sev_colors = {
        "GREEN": COLORS["green"],
        "YELLOW": COLORS["yellow"],
        "ORANGE": COLORS["orange"],
        "RED": COLORS["red"],
        "PURPLE": COLORS["purple"],
    }
    border_color = sev_colors.get(severity.upper(), COLORS["cyan"])
    bg_color = border_color + "10"

    policy_text = "APPROVED ✓" if policy_approved else "REJECTED ✗"
    policy_color = COLORS["green"] if policy_approved else COLORS["red"]

    badge_color = COLORS["green"] if status == "executed" else COLORS["orange"]

    html = f"""
    <style>
    .action-card-{action_type.replace(' ', '-').lower()} {{
        background: {bg_color};
        border: 1px solid {border_color}60;
        border-left: 4px solid {border_color};
        border-radius: 8px;
        padding: 12px 16px;
        margin: 4px 0;
        font-family: 'Courier New', monospace;
    }}
    .action-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }}
    .action-type {{
        color: {border_color};
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .action-confidence {{
        color: {COLORS['grey']};
        font-size: 11px;
    }}
    .action-reason {{
        color: {COLORS['grey']};
        font-size: 11px;
        margin: 4px 0;
        line-height: 1.4;
    }}
    .action-footer {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 6px;
    }}
    .action-impact {{
        color: {COLORS['cyan']};
        font-size: 12px;
        font-weight: 600;
    }}
    .policy-badge {{
        color: {policy_color};
        font-size: 11px;
        font-weight: 600;
    }}
    .status-badge {{
        background: {badge_color}30;
        color: {badge_color};
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 4px;
        text-transform: uppercase;
    }}
    </style>
    <div class="action-card-{action_type.replace(' ', '-').lower()}">
        <div class="action-header">
            <span class="action-type">[{severity}] {action_type}</span>
            <span class="status-badge">{status}</span>
        </div>
        <div class="action-confidence">Confidence: {confidence:.1f}%</div>
        <div class="action-reason">{reason}</div>
        <div class="action-footer">
            <span class="action-impact">Impact: +{impact:.1f}% KPI</span>
            <span class="policy-badge">{policy_text}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Agent Reasoning Panel ─────────────────────────────────────────────────────
def agent_reasoning_panel(entries: list) -> None:
    """Render a scrolling AI multi-agent reasoning console."""
    if not entries:
        st.info("No reasoning entries yet. Streaming will begin shortly...")
        return

    lines_html = ""
    for entry in entries[-20:]:  # Show last 20 entries
        color = COLORS.get(entry.get("color", "cyan"), COLORS["cyan"])
        agent = entry.get("agent_name", "Unknown")
        agent_type = entry.get("agent_type", "")
        reasoning = entry.get("reasoning", "")
        confidence = entry.get("confidence", 85.0)
        ts = entry.get("timestamp", "")[:19]

        lines_html += f"""
        <div style="
            border-left: 3px solid {color};
            margin: 4px 0;
            padding: 6px 12px;
            background: #0D1B2A;
            border-radius: 4px;
        ">
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
                <span style="color:{color}; font-family:'Courier New',monospace; font-size:12px; font-weight:700;">
                    [{agent_type}] {agent}
                </span>
                <span style="color:{COLORS['grey']}; font-family:'Courier New',monospace; font-size:10px;">
                    {ts}
                </span>
            </div>
            <div style="color:#E0E0E0; font-family:'Courier New',monospace; font-size:11px; line-height:1.5;">
                {reasoning}
            </div>
            <div style="color:{COLORS['grey']}; font-family:'Courier New',monospace; font-size:10px; margin-top:4px;">
                Confidence: {confidence:.1f}%
            </div>
        </div>
        """

    html = f"""
    <style>
    .reasoning-container {{
        background: #0A1428;
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px;
        max-height: 400px;
        overflow-y: auto;
    }}
    .reasoning-container::-webkit-scrollbar {{
        width: 6px;
    }}
    .reasoning-container::-webkit-scrollbar-track {{
        background: #0A1428;
    }}
    .reasoning-container::-webkit-scrollbar-thumb {{
        background: {COLORS['cyan']}60;
        border-radius: 3px;
    }}
    </style>
    <div class="reasoning-container">
        {lines_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Subscriber Card ─────────────────────────────────────────────────────────
def subscriber_card(subscriber: dict) -> None:
    """Render a VIP subscriber detail card."""
    vip_color = COLORS["red"] if subscriber.get("is_vip") else COLORS["cyan"]
    frustration = subscriber.get("frustration_index", 0)
    frus_color = COLORS["green"] if frustration < 30 else COLORS["orange"] if frustration < 60 else COLORS["red"]

    html = f"""
    <style>
    .sub-card {{
        background: #0D1B2A;
        border: 1px solid {vip_color}40;
        border-left: 3px solid {vip_color};
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
        font-family: 'Courier New', monospace;
    }}
    .sub-id {{
        color: {vip_color};
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 6px;
    }}
    .sub-row {{
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        padding: 2px 0;
        color: {COLORS['grey']};
    }}
    .sub-val {{
        color: #E0E0E0;
    }}
    </style>
    <div class="sub-card">
        <div class="sub-id">{'★ ' if subscriber.get('is_vip') else ''}{subscriber.get('ue_id', 'N/A')}</div>
        <div class="sub-row">
            <span>QoS Class</span><span class="sub-val">{subscriber.get('qos_class', 'N/A')}</span>
        </div>
        <div class="sub-row">
            <span>Frustration Index</span><span class="sub-val" style="color:{frus_color};">{frustration:.1f}</span>
        </div>
        <div class="sub-row">
            <span>Handovers</span><span class="sub-val">{subscriber.get('handover_count', 0)}</span>
        </div>
        <div class="sub-row">
            <span>QoE Degradation</span><span class="sub-val">{subscriber.get('qoe_degradation_predicted_min', 999):.1f} min</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Alert Banner ─────────────────────────────────────────────────────────────
def alert_banner(alert: dict) -> None:
    """Render a compact RAN alert banner."""
    sev_colors = {
        "GREEN": COLORS["green"],
        "YELLOW": COLORS["yellow"],
        "ORANGE": COLORS["orange"],
        "RED": COLORS["red"],
        "PURPLE": COLORS["purple"],
    }
    color = sev_colors.get(alert.get("severity", "CYAN").upper(), COLORS["cyan"])

    html = f"""
    <div style="
        background: {color}15;
        border: 1px solid {color}50;
        border-left: 3px solid {color};
        border-radius: 6px;
        padding: 8px 12px;
        margin: 3px 0;
        font-family: 'Courier New', monospace;
        font-size: 11px;
    ">
        <span style="color:{color}; font-weight:700;">[{alert.get('alert_type', 'ALERT')}]</span>
        <span style="color:{COLORS['grey']}; margin-left:8px;">{alert.get('reason', '')}</span>
        <span style="color:{color}; margin-left:8px; font-size:10px;">{alert.get('confidence', 0):.0f}%</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Congestion Gauge ─────────────────────────────────────────────────────────
def congestion_gauge(level: str, pct: float) -> None:
    """Render a text-based congestion gauge."""
    n = int(pct / 5)
    bar = "█" * n + "░" * (20 - n)
    color = COLORS["green"] if level == "GREEN" else COLORS["orange"] if level == "YELLOW" else COLORS["red"]
    label = "LOW" if level == "GREEN" else "MODERATE" if level == "YELLOW" else "HIGH"

    html = f"""
    <div style="font-family:'Courier New',monospace; font-size:12px;">
        <div style="margin-bottom:4px;">CONGESTION: <span style="color:{color}; font-weight:700;">{label}</span> {pct:.0f}%</div>
        <div style="color:{COLORS['grey']};">{bar}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ── Live Log Streamer ─────────────────────────────────────────────────────────
def live_log_display(log_lines: list[str]) -> None:
    """Render a scrolling live log display."""
    if not log_lines:
        return

    lines_html = "".join(
        f'<div style="color:{COLORS["grey"]}; font-family:\'Courier New\',monospace; '
        f'font-size:11px; padding:1px 0; border-bottom:1px solid #1A2A3A;">'
        f'{line}</div>'
        for line in log_lines[-30:]
    )

    html = f"""
    <div style="
        background: #0A1428;
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px;
        max-height: 200px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
    ">{lines_html}</div>
    """
    st.markdown(html, unsafe_allow_html=True)
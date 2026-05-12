"""
Async telemetry streamer for CovMo Telecom Intelligence Platform.

Generates synthetic UE telemetry every 500ms simulating the
Taipei Arena Concert Egress scenario (Power Station Concert, May 15, 2026).

The crowd moves from Taipei Arena → Nanjing Fuxing MRT exits.

INCIDENT ARCS (timeline over ~200 ticks / 100 seconds):
  Tick   1-30   : Nominal — crowd assembles, low activity
  Tick  30-60   : Mass egress begins, congestion rises
  Tick  40-80   : WEATHER SPIKE — rainfall 0 → 12 mm/hr
  Tick  50-100  : MULTI-CELL HANDOVER STORM (0.65 < phase < 0.80)
  Tick  80-120  : VIP DEGRADATION ARC — VIPs enter MRT underground
  Tick  100-150 : MRT OVERLOAD CASCADE — PRB > 90% at MRT DAS
  Tick  120-160 : ANOMALY BURST — CQI drops to 2-3 across 20% of UEs
  Tick  130-180 : SECONDARY CONGESTION — load-balancing action fires
  Tick  150-200 : YOUBIKE STARVATION — all docks empty, frustration peaks
  Tick  200+    : Nominal cooldown — crowd disperses, PRB recovers
"""
from __future__ import annotations

import asyncio
import json as _json
import random
import hashlib
import math
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Optional

import numpy as np

from models import (
    UETelemetry,
    UELocation,
    UEMetrics,
    EventType,
    QoSClass,
    SliceType,
    AutonomousAction,
    AgentReasoningEntry,
    AlertSeverity,
)
from config import TELEMETRY_INTERVAL_MS, SIMULATION_DENSITY
from services import (
    update_telemetry as _update_service_telemetry,
    analyze_ran_state,
    analyze_mobility,
    get_weather,
    validate_action,
    get_default_actions,
)
from services.ran_service import correlate_events
from services.telemetry_service import (
    save_replay_snapshot,
    start_monitoring,
    check_monitoring,
    stop_monitoring,
    get_monitoring_state,
    store_agent_reasoning,
)
from services.policy_engine import APPROVED_ACTION_TYPES


# ── Geographic Constants ──────────────────────────────────────────────────────
TAIPEI_ARENA = (25.0516, 121.5500)  # lat, lon
NANJING_FUXING_MRT = (25.0528, 121.5445)
YOUBIKE_ARENA = (25.0518, 121.5492)

# ── Cell IDs ───────────────────────────────────────────────────────────────────
CELLS = [
    ("TW_TPE_ARENA_01", "S1"),
    ("TW_TPE_ARENA_01", "S2"),
    ("TW_TPE_ARENA_01", "S3"),
    ("TW_TPE_ARENA_SC01", "SC1"),
    ("TW_TPE_ARENA_SC02", "SC2"),
    ("TW_TPE_MRT_NS_01", "MRT_S1"),
]


# ── Global Streamer State ─────────────────────────────────────────────────────
_tick: int = 0
_is_streaming: bool = False
_reasoning_log: List[AgentReasoningEntry] = []
_recent_actions: List[AutonomousAction] = []
_ran_alerts: List[Dict] = []

# ── ADK Integration State ─────────────────────────────────────────────────────
# Track which agents are in monitoring mode to avoid re-starting
_active_monitors: set[str] = set()
_last_snapshot_tick: int = 0
_last_red_alert_tick: int = -999
_last_vip_breach_tick: int = -999
_last_mass_egress_tick: int = -999
_action_history: list[str] = []  # for loop detection in policy engine


# ── Subscriber Pool ───────────────────────────────────────────────────────────
_VIP_IDS = [f"VIP_{i:03d}" for i in range(1, 16)]  # 15 VIP subscribers
_STANDARD_IDS = [f"STD_{i:04d}" for i in range(1, 200)]  # 199 standard


# ══════════════════════════════════════════════════════════════════════════════
# INCIDENT ARC CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
# These globals are modified by the streamer to drive scenario arcs.
# Reset each time streaming begins.
_incident_flags: dict = {}


def _reset_incidents():
    """Reset all incident state at stream start."""
    global _incident_flags, _active_monitors, _last_snapshot_tick
    global _last_red_alert_tick, _last_vip_breach_tick, _last_mass_egress_tick
    global _action_history
    _incident_flags = {
        "weather_spike_active": False,
        "handover_storm_active": False,
        "vip_degradation_active": False,
        "mrt_overload_active": False,
        "anomaly_burst_active": False,
        "youbike_starved": False,
        "secondary_congestion_active": False,
        "vip_sla_breach_triggered": False,
    }
    _active_monitors.clear()
    _last_snapshot_tick = 0
    _last_red_alert_tick = -999
    _last_vip_breach_tick = -999
    _last_mass_egress_tick = -999
    _action_history.clear()


def _tick_incident(tick: int) -> None:
    """Update incident flags based on current tick."""
    # Weather spike: tick 40-80, rainfall 0 → 12 mm/hr
    if 40 <= tick <= 80:
        _incident_flags["weather_spike_active"] = True
    # Handover storm: tick 50-100 (coincides with phase 0.65-0.80)
    if 50 <= tick <= 100:
        _incident_flags["handover_storm_active"] = True
    # VIP degradation: tick 80-120
    if 80 <= tick <= 120:
        _incident_flags["vip_degradation_active"] = True
    # MRT overload: tick 100-150
    if 100 <= tick <= 150:
        _incident_flags["mrt_overload_active"] = True
    # Anomaly burst: tick 120-160
    if 120 <= tick <= 160:
        _incident_flags["anomaly_burst_active"] = True
    # YouBike starvation: tick 150-200
    if 150 <= tick <= 200:
        _incident_flags["youbike_starved"] = True


# ── Weather Simulation (Dynamic) ─────────────────────────────────────────────
_weather_tick_override: dict = {}  # tick → WeatherState override


def _compute_dynamic_weather(tick: int):
    """Compute weather state based on tick (enables weather spike arc)."""
    from models import WeatherState
    # Base: light rain (7.2 mm/hr)
    base_rainfall = 7.2
    rainfall = base_rainfall

    if _incident_flags.get("weather_spike_active"):
        # Spike from 0 → 12 mm/hr at tick 40, sustain, taper at tick 80
        if tick < 40:
            rainfall = 0.0
        elif 40 <= tick <= 80:
            # Linear ramp: 0 → 12 mm/hr
            rainfall = min(12.0, (tick - 40) / 40 * 12.0)
        else:
            # Taper down
            rainfall = max(7.2, 12.0 - (tick - 80) * 0.1)
        rainfall = round(rainfall, 1)

    slip_risk = "LOW"
    if rainfall < 1.0:
        slip_risk = "LOW"
    elif rainfall < 5.0:
        slip_risk = "MODERATE"
    elif rainfall < 10.0:
        slip_risk = "HIGH"
    else:
        slip_risk = "SEVERE"

    walking_prop = 1.0
    if rainfall >= 1.0:
        walking_prop = 0.60 if rainfall < 10.0 else 0.30
    if rainfall >= 10.0:
        walking_prop = 0.30

    return WeatherState(
        timestamp=datetime.now(),
        rainfall_mm_hr=rainfall,
        temperature_c=24.5,
        humidity_pct=78.0,
        wind_speed_ms=2.3,
        condition="light_rain" if rainfall > 1 else "clear",
        source="dynamic_scenario",
    )


# ── Helpers ────────────────────────────────────────────────────────────────────
def _generate_ue_id() -> str:
    """Generate a hashed UE identifier."""
    raw = str(random.getrandbits(64)) + str(datetime.now().timestamp())
    return "UE_" + hashlib.md5(raw.encode()).hexdigest()[:8].upper()


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate Haversine distance in meters."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _interpolate_pos(
    t: float,
    start: tuple[float, float],
    end: tuple[float, float]
) -> tuple[float, float]:
    """Linearly interpolate position along a path."""
    return (
        start[0] + (end[0] - start[0]) * t,
        start[1] + (end[1] - start[1]) * t,
    )


# ── Telemetry Generation ──────────────────────────────────────────────────────
def _generate_single_ue_trace(
    ue_id: str,
    qos: QoSClass,
    stype: SliceType,
    tick: int,
    phase: float,
    is_vip: bool = False,
) -> UETelemetry:
    """
    Generate a single UE telemetry trace.

    phase: 0.0 = at arena, 1.0 = at MRT
    Incident arcs are injected based on tick and global _incident_flags.
    """
    # ── Position ─────────────────────────────────────────────────────────────
    pos = _interpolate_pos(phase, TAIPEI_ARENA, NANJING_FUXING_MRT)
    jitter = (random.uniform(-0.0002, 0.0002), random.uniform(-0.0002, 0.0002))
    lat, lon = pos[0] + jitter[0], pos[1] + jitter[1]
    dist_to_mrt = _distance_m(lat, lon, *NANJING_FUXING_MRT)

    # ── Cell Assignment ─────────────────────────────────────────────────────
    if phase > 0.75:
        cell_id, sector_id = "TW_TPE_MRT_NS_01", "MRT_S1"
    else:
        cell_id, sector_id = random.choice(CELLS[:5])

    # ── RAN Metrics ─────────────────────────────────────────────────────────
    # RSRP: -85 to -105 dBm
    base_rsrp = -88 if is_vip else -92

    # Arc 1: VIP degradation (tick 80-120, underground)
    underground_penalty = 12 if phase > 0.75 else 0
    vip_penalty = 6 if (is_vip and _incident_flags.get("vip_degradation_active")) else 0
    rsrp_noise = random.gauss(0, 2)
    rsrp = base_rsrp - underground_penalty - vip_penalty + rsrp_noise

    # Arc 2: Anomaly burst (tick 120-160) — CQI crashes for 20% of UEs
    cqi_base_modifier = 0
    if _incident_flags.get("anomaly_burst_active") and random.random() < 0.20:
        cqi_base_modifier = -10  # Crash CQI to 2-3

    # SINR: 10-18 dB
    base_sinr = 16 if is_vip else 12
    sinr = max(3, base_sinr - (phase * 8) + random.gauss(0, 1.5))

    # Arc 3: MRT overload — PRB spikes above 90% at MRT DAS (tick 100-150)
    base_prb = 45 + (phase * 35)
    if _incident_flags.get("mrt_overload_active") and phase > 0.75:
        base_prb = min(99, base_prb + 20)  # Extra 20% PRB from overload
    prb = min(99, base_prb + random.gauss(0, 5))

    # Arc 4: Multi-cell handover storm (tick 50-100, phase 0.65-0.80)
    base_ta = 10
    ta = int(base_ta + phase * 30 + random.gauss(0, 3))
    ta = max(1, min(63, ta))

    # Timing advance and AOA
    aoa_base = 172 + (phase * 30)
    aoa_variance = 40 if phase < 0.4 else 15
    aoa = (aoa_base + random.gauss(0, aoa_variance)) % 360

    # Throughput
    if is_vip:
        base_tp = random.uniform(80, 120)
    else:
        base_tp = random.uniform(40, 90)
    tp = max(5, base_tp * (sinr / 20) * (1 - phase * 0.3))

    # Handover: Arc 4 — elevated failure rate during handover storm
    ho_success = True
    if _incident_flags.get("handover_storm_active") and 0.65 < phase < 0.80:
        ho_success = random.random() > 0.30  # 30% failure during storm
    elif 0.65 < phase < 0.80:
        ho_success = random.random() > 0.12
    else:
        ho_success = random.random() > 0.02

    retrans = random.uniform(0.01, 0.06) if phase > 0.7 else random.uniform(0.01, 0.03)

    # CQI: Arc 2 anomaly burst
    cqi = max(1, min(15, int(13 - phase * 8 + random.gauss(0, 1) + cqi_base_modifier)))

    # Event type
    event = EventType.RRC_MEASUREMENT_REPORT
    if not ho_success:
        event = EventType.HANDOVER_REQUEST
    if prb > 80:
        event = EventType.CONGESTION_DETECTED
    if phase > 0.75 and rsrp < -100:
        event = EventType.SIGNAL_CLIFF

    return UETelemetry(
        timestamp=datetime.now(timezone.utc),
        ue_id=ue_id,
        qos_class=qos,
        slice_type=stype,
        cell_id=cell_id,
        sector_id=sector_id,
        event=event,
        metrics=UEMetrics(
            rsrp=round(rsrp, 1),
            sinr=round(sinr, 1),
            ta=ta,
            aoa=round(aoa, 1),
            throughput_mbps=round(tp, 1),
            handover_success=ho_success,
            packet_retransmission_rate=round(retrans, 4),
            prb_utilization=round(prb, 1),
            cqi=cqi,
        ),
        location=UELocation(lat=round(lat, 6), lon=round(lon, 6)),
        distance_to_mrt_m=round(dist_to_mrt, 1),
    )


def _generate_batch(tick: int) -> List[UETelemetry]:
    """Generate a batch of UE telemetry traces with incident arcs."""
    global _VIP_IDS, _STANDARD_IDS

    batch: List[UETelemetry] = []
    n = SIMULATION_DENSITY

    # ── Phase calculation ──────────────────────────────────────────────────
    raw_phase = min(1.0, (tick * 0.006))
    phase_noise = lambda: random.uniform(-0.05, 0.05)

    # ── VIP Subscribers ──────────────────────────────────────────────────────
    vip_qos = QoSClass.VIP_PREMIUM
    vip_slice = SliceType.VIP_SLICE
    for vid in _VIP_IDS:
        phase = min(1.0, max(0.0, raw_phase + phase_noise() + random.uniform(0, 0.15)))
        batch.append(_generate_single_ue_trace(vid, vip_qos, vip_slice, tick, phase, is_vip=True))

    # ── Standard Subscribers ───────────────────────────────────────────────
    active_standard = min(len(_STANDARD_IDS), max(10, int(n * 3)))
    std_qos = QoSClass.STANDARD
    std_slice = SliceType.STANDARD_SLICE

    for i in range(active_standard):
        sid = _STANDARD_IDS[i]
        lag = random.uniform(0, 0.25)
        phase = min(1.0, max(0.0, raw_phase + phase_noise() - lag))
        batch.append(_generate_single_ue_trace(sid, std_qos, std_slice, tick, phase, is_vip=False))

    return batch


# ── Autonomous Action Lifecycle ────────────────────────────────────────────────
def _build_action_proposal(
    tick: int,
    reason: str,
    action_type: str,
    confidence: float,
    kpi_improvement: float,
    congestion_reduction: float,
) -> Optional[AutonomousAction]:
    """Build and policy-validate an autonomous action proposal."""
    action = AutonomousAction(
        action_id=f"act_{tick:04d}_{action_type[:4]}",
        action_type=action_type,
        timestamp=datetime.now(),
        confidence_score=confidence,
        reason=reason,
        expected_kpi_improvement_pct=kpi_improvement,
        expected_congestion_reduction_pct=congestion_reduction,
        status="proposed",
    )

    decision = validate_action(action)

    if decision.approved:
        action.policy_approved = True
        action.status = "approved"
        # Execute immediately (simulated)
        action.executed = True
        action.status = "executed"
        global _action_history
        _action_history.append(action_type)
        # Keep last 20 action types for loop detection
        if len(_action_history) > 20:
            _action_history = _action_history[-20:]
        return action
    else:
        action.policy_approved = False
        action.policy_reject_reason = decision.reasoning
        action.status = "rejected"
        return action


def _propose_and_validate_actions(
    tick: int,
    ran_alerts: List[Dict],
    mobility_state: dict,
    correlated_events: List[dict],
) -> List[AutonomousAction]:
    """Propose, validate, and execute autonomous actions based on current state."""
    global _last_vip_breach_tick
    actions: List[AutonomousAction] = []

    # Loop detection: don't propose same action twice in 15 ticks
    recent_action_types = set(_action_history[-15:])

    # ── Action 1: VIP PRIORITY ROUTING ─────────────────────────────────────────
    # Triggered by VIP degradation arc (tick 80+) or correlated VIP event
    vip_event = next(
        (e for e in correlated_events
         if e.get("scenario_label") == "VIP_QOE_DEGRADATION_RISK"),
        None
    )
    if vip_event and "VIP_PRIORITY_ROUTING" not in recent_action_types:
        action = _build_action_proposal(
            tick=tick,
            reason=(
                f"VIP QoE degradation risk detected. "
                f"Confidence: {vip_event.get('confidence', 0):.0f}%. "
                f"Action: reroute VIP traffic to alternate slice."
            ),
            action_type="VIP_PRIORITY_ROUTING",
            confidence=vip_event.get("confidence", 88.0),
            kpi_improvement=23.0,
            congestion_reduction=0.0,
        )
        if action:
            actions.append(action)
        _last_vip_breach_tick = tick

    # ── Action 2: TEMPORARY LOAD BALANCING ────────────────────────────────────
    # Triggered by MRT overload arc or PRB congestion event
    prb_event = next(
        (e for e in correlated_events
         if e.get("scenario_label") == "PRB_CELL_CONGESTION"),
        None
    )
    mass_egress = mobility_state.get("mass_egress_detected", False)
    if (prb_event or (mass_egress and tick > 50)) and \
            "TEMPORARY_LOAD_BALANCING" not in recent_action_types:
        action = _build_action_proposal(
            tick=tick,
            reason=(
                f"MRT cell PRB saturation. Mass egress confirmed. "
                f"Balancing load to arena macro cells."
            ),
            action_type="TEMPORARY_LOAD_BALANCING",
            confidence=88.0,
            kpi_improvement=15.0,
            congestion_reduction=18.0,
        )
        if action:
            actions.append(action)

    # ── Action 3: SMALL CELL STEERING ─────────────────────────────────────────
    # Triggered by underground transition or signal cliff
    underground_event = next(
        (e for e in correlated_events
         if e.get("scenario_label") in ("MRT_UNDERGROUND_TRANSITION",
                                         "SIGNAL_CLIFF_UNDERGROUND_TRANSITION")),
        None
    )
    if underground_event and "SMALL_CELL_STEERING" not in recent_action_types:
        action = _build_action_proposal(
            tick=tick,
            reason=(
                f"Underground MRT transition detected. "
                f"RSRP cliff likely. Steering UEs to MRT DAS micro-cell."
            ),
            action_type="SMALL_CELL_STEERING",
            confidence=85.0,
            kpi_improvement=12.0,
            congestion_reduction=0.0,
        )
        if action:
            actions.append(action)

    # ── Action 4: DYNAMIC SLICE ALLOCATION ────────────────────────────────────
    # Triggered by congestion + mass egress
    if mass_egress and prb_event and "DYNAMIC_SLICE_ALLOCATION" not in recent_action_types:
        action = _build_action_proposal(
            tick=tick,
            reason=(
                f"PRB congestion during mass egress. "
                f"Dynamic slice reallocation to accommodate surge."
            ),
            action_type="DYNAMIC_SLICE_ALLOCATION",
            confidence=82.0,
            kpi_improvement=8.0,
            congestion_reduction=10.0,
        )
        if action:
            actions.append(action)

    return actions


# ── Incident Replay ───────────────────────────────────────────────────────────
def _save_incident_snapshot(
    tick: int,
    kpis: dict,
    reasoning_entries: List[Dict],
    executed_actions: List[Dict],
) -> None:
    """Save a replay snapshot at an incident boundary."""
    global _last_snapshot_tick
    if tick - _last_snapshot_tick >= 5:  # Debounce: max 1 per 5 ticks
        save_replay_snapshot(reasoning_log=reasoning_entries)
        _last_snapshot_tick = tick


# ── Continuous Monitoring ──────────────────────────────────────────────────────
def _check_monitoring_escalation(
    tick: int,
    ran_alerts: List[Dict],
    mobility_state: dict,
    correlated_events: List[dict],
) -> Dict[str, dict]:
    """Run monitoring checks for all active agents. Returns escalation state."""
    escalations = {}

    agents = [
        ("ran_intelligence_agent", ran_alerts, "RAN"),
        ("mobility_intelligence_agent", [mobility_state] if mobility_state else [],
         "MOBILITY"),
        ("context_intelligence_agent", correlated_events, "CONTEXT"),
        ("policy_validation_agent", [], "POLICY"),
    ]

    for agent_name, alert_source, agent_type in agents:
        # Start monitoring when conditions warrant
        if agent_name not in _active_monitors:
            if _should_start_monitoring(agent_name, alert_source, mobility_state):
                result = start_monitoring(agent_name)
                _active_monitors.add(agent_name)

        # Run check if monitoring is active
        if agent_name in _active_monitors:
            # Determine top severity
            severity = "YELLOW"
            alert_type = None
            if alert_source:
                # Pick the most severe alert
                for item in alert_source:
                    if isinstance(item, dict):
                        sev = item.get("severity", "YELLOW")
                        if sev == "RED":
                            severity = "RED"
                            alert_type = item.get("alert_type", alert_type)
                            break
                        elif sev == "ORANGE" and severity != "RED":
                            severity = "ORANGE"
                            alert_type = item.get("alert_type", alert_type)

            result = check_monitoring(agent_name, alert_type, severity)
            escalations[agent_name] = result

    return escalations


def _should_start_monitoring(agent_name: str, alerts: list, mobility_state: dict) -> bool:
    """Determine if monitoring should start for an agent."""
    if agent_name == "ran_intelligence_agent":
        return any(a.get("severity") in ("ORANGE", "RED") for a in alerts)
    if agent_name == "mobility_intelligence_agent":
        return mobility_state.get("mass_egress_detected", False)
    if agent_name == "context_intelligence_agent":
        return any(
            e.get("scenario_label") in ("MRT_UNDERGROUND_TRANSITION",
                                         "VIP_QOE_DEGRADATION_RISK")
            for e in alerts
        )
    if agent_name == "policy_validation_agent":
        return any(a.get("severity") == "RED" for a in alerts)
    return False


# ── Correlated Events ─────────────────────────────────────────────────────────
def _compute_correlated_events(
    telemetry_batch: List[UETelemetry],
    mobility_state,
    weather_state,
) -> List[dict]:
    """Compute correlated events using the RAN service correlation engine."""
    vip_count = sum(1 for t in telemetry_batch if t.qos_class == QoSClass.VIP_PREMIUM)
    vip_ratio = vip_count / len(telemetry_batch) if telemetry_batch else 0.0
    prb_vals = [t.metrics.prb_utilization for t in telemetry_batch]
    avg_prb = sum(prb_vals) / len(prb_vals) if prb_vals else 0.0

    events = correlate_events(
        telemetry_batch=telemetry_batch,
        mobility_state=mobility_state,
        weather_state=weather_state,
        vip_density_ratio=vip_ratio,
        congestion_prb_pct=avg_prb,
    )

    return [e.model_dump(mode="json") for e in events]


# ── AI Reasoning Entry ────────────────────────────────────────────────────────
def _build_reasoning_entry(
    tick: int,
    adk_output: Optional[dict],
    correlated_events: List[dict],
    actions: List[AutonomousAction],
    escalation: dict,
) -> AgentReasoningEntry:
    """Build the final reasoning entry for the console display."""
    from models import CorrelatedEvent, AlertSeverity

    # Use real ADK output if available
    if adk_output:
        return AgentReasoningEntry(
            timestamp=datetime.now(),
            agent_name="CovMo Intent Orchestrator",
            agent_type=adk_output.get("agent_type", "INTENT"),
            reasoning=adk_output.get("reasoning", "Streaming analysis active."),
            confidence=adk_output.get("confidence", 75.0),
            triggered_action=adk_output.get("triggered_action"),
            color=adk_output.get("color", "cyan"),
        )

    # Fallback: deterministic reasoning based on correlated events
    if correlated_events:
        top = max(correlated_events,
                  key=lambda e: {"RED": 4, "ORANGE": 3, "YELLOW": 2,
                                 "GREEN": 1}.get(e.get("severity", ""), 0))
        severity = top.get("severity", "")
        scenario = top.get("scenario_label", "UNKNOWN")
        action = top.get("recommended_autonomous_action")

        color_map = {"RED": "red", "ORANGE": "orange", "YELLOW": "green",
                     "GREEN": "cyan"}
        color = color_map.get(severity, "cyan")

        if scenario == "VIP_QOE_DEGRADATION_RISK":
            signals = top.get("signal_correlation", {})
            return AgentReasoningEntry(
                timestamp=datetime.now(),
                agent_name="CovMo RAN Intelligence",
                agent_type="RAN",
                reasoning=(
                    f"VIP SLA violation risk. QoE: {signals.get('vip_qoe_estimate', '?')}/100. "
                    f"RSRP avg: {signals.get('vip_rsrp_avg', '?')} dBm. Confidence: "
                    f"{top.get('confidence', 0):.0f}%. Recommended: {action}"
                ),
                confidence=top.get("confidence", 85.0),
                triggered_action=action,
                color=color,
            )
        elif scenario == "MRT_UNDERGROUND_TRANSITION":
            signals = top.get("signal_correlation", {})
            return AgentReasoningEntry(
                timestamp=datetime.now(),
                agent_name="CovMo MOBILITY Engine",
                agent_type="MOBILITY",
                reasoning=(
                    f"MRT underground transition. RSRP avg: {signals.get('avg_rsrp', '?')} dBm. "
                    f"Low SINR ratio: {signals.get('low_sinr_ratio', '?')}. "
                    f"Rainfall: {signals.get('rainfall_mm_hr', '?')} mm/hr. "
                    f"Recommended: {action}"
                ),
                confidence=top.get("confidence", 80.0),
                triggered_action=action,
                color="orange",
            )
        elif scenario == "PRB_CELL_CONGESTION":
            signals = top.get("signal_correlation", {})
            return AgentReasoningEntry(
                timestamp=datetime.now(),
                agent_name="CovMo AUTONOMOUS Engine",
                agent_type="AUTONOMOUS",
                reasoning=(
                    f"PRB congestion at {signals.get('avg_prb_pct', '?')}%. "
                    f"Max PRB: {signals.get('max_prb', '?')}%. "
                    f"TA rising pct: {signals.get('ta_rising_pct', '?')}. "
                    f"Recommended: {action}"
                ),
                confidence=top.get("confidence", 88.0),
                triggered_action=action,
                color="red",
            )
        elif scenario == "MASS_EGRESS_CONFIRMED":
            signals = top.get("signal_correlation", {})
            return AgentReasoningEntry(
                timestamp=datetime.now(),
                agent_name="CovMo MOBILITY Engine",
                agent_type="MOBILITY",
                reasoning=(
                    f"Mass egress confirmed. {signals.get('ta_rising_pct', '?')*100:.0f}% "
                    f"subscribers with rising TA. Egress velocity: "
                    f"{signals.get('egress_velocity_kmh', '?')} km/h. "
                    f"MRT congestion: {signals.get('overall_congestion', '?')}. "
                    f"Rainfall: {signals.get('rainfall', '?')} mm/hr. "
                    f"Recommended: {action}"
                ),
                confidence=top.get("confidence", 88.0),
                triggered_action=action,
                color="orange",
            )
        else:
            return AgentReasoningEntry(
                timestamp=datetime.now(),
                agent_name="CovMo Event Engine",
                agent_type="INTENT",
                reasoning=(
                    f"{scenario} detected. "
                    f"Confidence: {top.get('confidence', 0):.0f}%. "
                    f"Consequence: {top.get('inferred_consequence', '?')}"
                ),
                confidence=top.get("confidence", 80.0),
                triggered_action=action,
                color=color,
            )

    # Nominal state
    return AgentReasoningEntry(
        timestamp=datetime.now(),
        agent_name="CovMo INTENT Engine",
        agent_type="INTENT",
        reasoning="System nominal. Monitoring crowd egress. All KPIs within normal range.",
        confidence=80.0,
        color="cyan",
    )


# ── Async Generator ───────────────────────────────────────────────────────────
async def stream_telemetry() -> AsyncGenerator[Dict, None]:
    """
    Async generator that yields telemetry batches as SSE events.

    Yields dicts with keys:
      telemetry, ran_alerts, mobility, weather, correlated_events,
      reasoning, actions, monitoring_escalations, active_ues, tick
    """
    global _tick, _is_streaming, _reasoning_log, _recent_actions
    global _ran_alerts, _active_monitors, _last_red_alert_tick
    global _last_vip_breach_tick, _last_mass_egress_tick

    _reset_incidents()
    _is_streaming = True
    _tick = 0

    # ADK client lazy import
    try:
        from adk_runner import run_agent_analysis
        ADK_RUNNER_AVAILABLE = True
    except ImportError:
        ADK_RUNNER_AVAILABLE = False

    while _is_streaming:
        _tick += 1
        _tick_incident(_tick)  # Update incident flags

        # ── Weather (dynamic, supports spike arc) ────────────────────────────
        weather = _compute_dynamic_weather(_tick)

        # ── Telemetry generation ──────────────────────────────────────────────
        telemetry_batch = _generate_batch(_tick)
        _update_service_telemetry(telemetry_batch)

        # ── RAN alerts ───────────────────────────────────────────────────────
        ran_alerts = analyze_ran_state(telemetry_batch)
        _ran_alerts = [
            {
                "alert_type": a.alert_type,
                "severity": a.severity.value,
                "reason": a.reason,
                "confidence": a.confidence_score,
                "action": a.recommended_action,
            }
            for a in ran_alerts
        ]

        # ── Mobility ─────────────────────────────────────────────────────────
        mobility = analyze_mobility(telemetry_batch, weather, crowd_size=1500, tick=_tick)
        mobility_dict = mobility.model_dump(mode="json")

        # ── Correlated Events (wired into stream) ────────────────────────────
        correlated_events = _compute_correlated_events(telemetry_batch, mobility, weather)

        # ── AI Agent Analysis (every 5 ticks to manage cost) ─────────────────
        adk_output = None
        if ADK_RUNNER_AVAILABLE and _tick % 5 == 0:
            try:
                kpis = {
                    "subscriber_satisfaction_score": 80.0,
                    "vip_qoe_score": 85.0,
                    "congestion_risk": 30.0,
                    "sla_health": 90.0,
                    "predicted_mobility_pressure": 50.0,
                }
                adk_output = await run_agent_analysis(
                    tick=_tick,
                    telemetry_context={"active_ues": len(telemetry_batch), "kpis": kpis},
                    ran_alerts=_ran_alerts,
                    mobility_state=mobility_dict,
                    weather_state=weather.model_dump(mode="json"),
                    correlated_events=correlated_events,
                )
            except Exception:
                pass  # Degrade gracefully — ADK call failed, use fallback

        # ── Reasoning entry (ADK or deterministic fallback) ────────────────
        reasoning_entry = _build_reasoning_entry(
            _tick, adk_output, correlated_events, _recent_actions, {}
        )
        _reasoning_log.append(reasoning_entry)
        if len(_reasoning_log) > 50:
            _reasoning_log = _reasoning_log[-50:]

        # Store in agent memory service
        try:
            store_agent_reasoning(
                agent_name="intent_orchestration_agent",
                agent_type=reasoning_entry.agent_type,
                reasoning=reasoning_entry.reasoning,
                confidence=reasoning_entry.confidence,
                triggered_action=reasoning_entry.triggered_action,
                color=reasoning_entry.color,
            )
        except Exception:
            pass

        # ── Autonomous Actions (policy-validated lifecycle) ──────────────────
        if _tick % 10 == 0:
            _recent_actions = _propose_and_validate_actions(
                _tick, _ran_alerts, mobility_dict, correlated_events
            )

        # ── Continuous Monitoring Loop ─────────────────────────────────────
        escalations = _check_monitoring_escalation(
            _tick, _ran_alerts, mobility_dict, correlated_events
        )

        # ── Incident Replay Snapshots ────────────────────────────────────────
        # Save at: first RED alert, VIP breach, mass egress, after actions
        has_red = any(a.get("severity") == "RED" for a in _ran_alerts)
        has_vip_breach = any(
            e.get("scenario_label") == "VIP_QOE_DEGRADATION_RISK"
            for e in correlated_events
        )
        mass_egress = mobility_dict.get("mass_egress_detected", False)
        has_executed_action = any(a.executed for a in _recent_actions)

        if (has_red and _tick - _last_red_alert_tick >= 15) or \
                (has_vip_breach and _tick - _last_vip_breach_tick >= 20) or \
                (mass_egress and _tick - _last_mass_egress_tick >= 25) or \
                has_executed_action:
            _save_incident_snapshot(
                _tick,
                kpis={},
                reasoning_entries=[r.model_dump(mode="json") for r in _reasoning_log[-5:]],
                executed_actions=[a.model_dump(mode="json") for a in _recent_actions
                                 if a.executed],
            )
            if has_red:
                _last_red_alert_tick = _tick
            if has_vip_breach:
                _last_vip_breach_tick = _tick
            if mass_egress:
                _last_mass_egress_tick = _tick

        # ── Yield SSE Payload ────────────────────────────────────────────────
        payload = {
            "tick": _tick,
            "timestamp": datetime.now().isoformat(),
            "telemetry": [t.model_dump(mode="json") for t in telemetry_batch],
            "ran_alerts": _ran_alerts,
            "mobility": mobility_dict,
            "weather": weather.model_dump(mode="json"),
            "correlated_events": correlated_events,
            "reasoning": [r.model_dump(mode="json") for r in _reasoning_log[-10:]],
            "actions": [a.model_dump(mode="json") for a in _recent_actions[-6:]],
            "monitoring_escalations": escalations,
            "active_ues": len(telemetry_batch),
            "incident_arcs": {
                flag: val for flag, val in _incident_flags.items() if val
            },
        }

        yield payload

        # ── Tick interval ───────────────────────────────────────────────────
        await asyncio.sleep(TELEMETRY_INTERVAL_MS / 1000.0)


# ── Control Functions ─────────────────────────────────────────────────────────
def stop_stream():
    global _is_streaming
    _is_streaming = False
    for agent_name in list(_active_monitors):
        try:
            stop_monitoring(agent_name)
        except Exception:
            pass


def is_streaming() -> bool:
    return _is_streaming


def get_latest_payload() -> Optional[Dict]:
    """Return the most recent payload (for non-SSE consumers)."""
    from services.telemetry_service import get_current_state
    state = get_current_state()
    return {
        "tick": _tick,
        "ran_alerts": _ran_alerts,
        "actions": [a.model_dump(mode="json") for a in _recent_actions],
        "reasoning": [r.model_dump(mode="json") for r in _reasoning_log[-10:]],
        "monitoring_escalations": {name: get_monitoring_state(name)
                                  for name in _active_monitors},
        "correlated_events": [],  # Filled in on-demand from correlate_events
        "incident_arcs": {flag: val for flag, val in _incident_flags.items() if val},
    }
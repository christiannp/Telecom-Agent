"""
Async telemetry streamer for CovMo Telecom Intelligence Platform.

Generates synthetic UE telemetry every 500ms simulating the
Taipei Arena Concert Egress scenario (Power Station Concert, May 15, 2026).

The crowd moves from Taipei Arena → Nanjing Fuxing MRT exits.
"""
from __future__ import annotations

import asyncio
import json
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


# ── Subscriber Pool ───────────────────────────────────────────────────────────
_VIP_IDS = [f"VIP_{i:03d}" for i in range(1, 16)]  # 15 VIP subscribers
_STANDARD_IDS = [f"STD_{i:04d}" for i in range(1, 200)]  # 199 standard


def _generate_ue_id() -> str:
    """Generate a hashed UE identifier."""
    raw = str(random.getrandbits(64)) + str(datetime.now().timestamp())
    return "UE_" + hashlib.md5(raw.encode()).hexdigest()[:8].upper()


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate Haversine distance in meters."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi/2)**2 +
         math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


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
    """
    # ── Position ─────────────────────────────────────────────────────────────
    pos = _interpolate_pos(phase, TAIPEI_ARENA, NANJING_FUXING_MRT)
    jitter = (random.uniform(-0.0002, 0.0002), random.uniform(-0.0002, 0.0002))
    lat, lon = pos[0] + jitter[0], pos[1] + jitter[1]
    dist_to_mrt = _distance_m(lat, lon, *NANJING_FUXING_MRT)

    # ── Cell Assignment ─────────────────────────────────────────────────────
    # Underground near MRT → MRT DAS cell; elsewhere → Arena cells
    if phase > 0.75:
        cell_id, sector_id = "TW_TPE_MRT_NS_01", "MRT_S1"
    else:
        cell_id, sector_id = random.choice(CELLS[:5])

    # ── RAN Metrics ─────────────────────────────────────────────────────────
    # RSRP: -85 to -105 dBm, degrades as UE moves to MRT underground
    base_rsrp = -88 if is_vip else -92
    underground_penalty = 12 if phase > 0.75 else 0
    noise = random.gauss(0, 2)
    rsrp = base_rsrp - underground_penalty + noise

    # SINR: 10-18 dB, degrades underground
    base_sinr = 16 if is_vip else 12
    sinr = max(3, base_sinr - (phase * 8) + random.gauss(0, 1.5))

    # Timing Advance: increases as crowd approaches MRT
    base_ta = 10
    ta = int(base_ta + phase * 30 + random.gauss(0, 3))
    ta = max(1, min(63, ta))

    # AOA: higher variance near arena (multi-path), stable near MRT
    aoa_base = 172 + (phase * 30)
    aoa_variance = 40 if phase < 0.4 else 15
    aoa = (aoa_base + random.gauss(0, aoa_variance)) % 360

    # Throughput: VIP gets better throughput
    if is_vip:
        base_tp = random.uniform(80, 120)
    else:
        base_tp = random.uniform(40, 90)
    tp = max(5, base_tp * (sinr / 20) * (1 - phase * 0.3))

    # PRB: increases with congestion as crowd grows
    base_prb = 45 + (phase * 35)
    prb = min(99, base_prb + random.gauss(0, 5))

    # Handover: higher failure chance near underground transition
    if 0.65 < phase < 0.80:
        ho_success = random.random() > 0.12
    else:
        ho_success = random.random() > 0.02

    retrans = random.uniform(0.01, 0.06) if phase > 0.7 else random.uniform(0.01, 0.03)

    # CQI: 0-15, better near arena
    cqi = max(1, min(15, int(13 - phase * 8 + random.gauss(0, 1))))

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
    """Generate a batch of UE telemetry traces."""
    global _VIP_IDS, _STANDARD_IDS

    batch: List[UETelemetry] = []
    n = SIMULATION_DENSITY

    # ── Phase calculation ──────────────────────────────────────────────────
    # Gradually increase crowd egress over time
    raw_phase = min(1.0, (tick * 0.006))
    # Add per-UE variation
    phase_noise = lambda: random.uniform(-0.05, 0.05)

    # ── VIP Subscribers (fixed pool, always included) ────────────────────────
    vip_qos = QoSClass.VIP_PREMIUM
    vip_slice = SliceType.VIP_SLICE
    for vid in _VIP_IDS:
        phase = min(1.0, max(0.0, raw_phase + phase_noise() + random.uniform(0, 0.15)))
        batch.append(_generate_single_ue_trace(vid, vip_qos, vip_slice, tick, phase, is_vip=True))

    # ── Standard Subscribers (varying pool) ─────────────────────────────────
    # Start with fewer, ramp up to full density
    active_standard = min(len(_STANDARD_IDS), max(10, int(n * 3)))
    std_qos = QoSClass.STANDARD
    std_slice = SliceType.STANDARD_SLICE

    for i in range(active_standard):
        sid = _STANDARD_IDS[i]
        # Some subscribers lag behind (lower phase)
        lag = random.uniform(0, 0.25)
        phase = min(1.0, max(0.0, raw_phase + phase_noise() - lag))
        batch.append(_generate_single_ue_trace(sid, std_qos, std_slice, tick, phase, is_vip=False))

    return batch


# ── Async Generator ──────────────────────────────────────────────────────────
async def stream_telemetry() -> AsyncGenerator[Dict, None]:
    """
    Async generator that yields telemetry batches as SSE events.

    Yields dicts with keys: telemetry, kpis, mobility, weather, alerts, reasoning, actions
    """
    global _tick, _is_streaming, _reasoning_log, _recent_actions, _ran_alerts

    _is_streaming = True
    _tick = 0

    weather = await get_weather()
    crowd_size = 1500  # Concert audience estimate

    while _is_streaming:
        _tick += 1

        # ── Generate telemetry ────────────────────────────────────────────────
        telemetry_batch = _generate_batch(_tick)

        # ── Update service state ────────────────────────────────────────────
        _update_service_telemetry(telemetry_batch)

        # ── AI analysis ──────────────────────────────────────────────────────
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

        mobility = analyze_mobility(telemetry_batch, weather, crowd_size, _tick)

        # ── Generate AI reasoning ────────────────────────────────────────────
        reasoning = _generate_reasoning(telemetry_batch, ran_alerts, mobility, weather)
        _reasoning_log.append(reasoning)
        if len(_reasoning_log) > 50:
            _reasoning_log = _reasoning_log[-50:]

        # ── Autonomous actions ────────────────────────────────────────────────
        if _tick % 10 == 0:  # Every ~5 seconds
            _recent_actions = _generate_actions(ran_alerts, mobility)
            _recent_actions = [
                a for a in _recent_actions
                if validate_action(a).approved
            ]

        # ── Yield SSE payload ──────────────────────────────────────────────
        payload = {
            "tick": _tick,
            "timestamp": datetime.now().isoformat(),
            "telemetry": [t.model_dump(mode="json") for t in telemetry_batch],
            "ran_alerts": _ran_alerts,
            "mobility": mobility.model_dump(mode="json"),
            "weather": weather.model_dump(mode="json"),
            "reasoning": [r.model_dump(mode="json") for r in _reasoning_log[-10:]],
            "actions": [a.model_dump(mode="json") for a in _recent_actions[-6:]],
            "active_ues": len(telemetry_batch),
        }

        yield payload

        # ── Tick interval ───────────────────────────────────────────────────
        await asyncio.sleep(TELEMETRY_INTERVAL_MS / 1000.0)


def _generate_reasoning(
    telemetry_batch,
    ran_alerts,
    mobility,
    weather,
) -> AgentReasoningEntry:
    """Generate an AI reasoning entry for the console display."""
    timestamp = datetime.now()

    # Determine dominant alert
    if ran_alerts:
        top = max(ran_alerts, key=lambda a: _severity_weight(a.severity))
    else:
        top = None

    agent_type = "RAN"
    color = "cyan"

    if mobility.mass_egress_detected:
        agent_type = "MOBILITY"
        color = "orange"
        reasoning = (
            f"Mass egress pattern confirmed. "
            f"Crowd density at MRT: {mobility.crowd_density_mrt}. "
            f"Egress velocity: {mobility.egress_velocity_kmh:.1f} km/h. "
            f"MRT congestion level: {mobility.overall_congestion}."
        )
    elif top and top.severity == AlertSeverity.RED:
        agent_type = "AUTONOMOUS"
        color = "green"
        reasoning = (
            f"Critical alert: {top.alert_type}. "
            f"{top.reason}. "
            f"Recommended: {top.recommended_action}"
        )
    elif weather.rainfall_mm_hr > 5:
        agent_type = "CONTEXT"
        color = "purple"
        reasoning = (
            f"Weather impact: Rainfall {weather.rainfall_mm_hr:.1f} mm/hr detected. "
            f"Slip risk: {mobility.slip_risk}. "
            f"MRT preference increased by {int((1-mobility.walking_propensity)*100)}%. "
            f"Walking propensity: {mobility.walking_propensity:.0%}"
        )
    elif top:
        reasoning = f"{top.alert_type}: {top.reason}"
    else:
        agent_type = "INTENT"
        color = "cyan"
        reasoning = "System nominal. Monitoring crowd egress. All KPIs within normal range."

    return AgentReasoningEntry(
        timestamp=timestamp,
        agent_name=f"CovMo {agent_type} Engine",
        agent_type=agent_type,
        reasoning=reasoning,
        confidence=85.0 + random.uniform(0, 10),
        color=color,
    )


def _severity_weight(severity: AlertSeverity) -> int:
    weights = {AlertSeverity.RED: 4, AlertSeverity.ORANGE: 3,
               AlertSeverity.YELLOW: 2, AlertSeverity.GREEN: 1}
    return weights.get(severity, 0)


def _generate_actions(ran_alerts, mobility) -> List[AutonomousAction]:
    """Generate autonomous actions based on current state."""
    global _tick
    actions = get_default_actions()

    if mobility.mass_egress_detected:
        actions[1].confidence_score = min(95, actions[1].confidence_score + 5)

    if any(a.severity == AlertSeverity.RED for a in ran_alerts):
        actions[0].confidence_score = min(95, actions[0].confidence_score + 3)
        actions[0].status = "proposed"

    return actions


# ── Control Functions ─────────────────────────────────────────────────────────
def stop_stream():
    global _is_streaming
    _is_streaming = False


def is_streaming() -> bool:
    return _is_streaming


def get_latest_payload() -> Optional[Dict]:
    """Return the most recent payload (for non-SSE consumers)."""
    return {
        "tick": _tick,
        "ran_alerts": _ran_alerts,
        "actions": [a.model_dump(mode="json") for a in _recent_actions],
        "reasoning": [r.model_dump(mode="json") for r in _reasoning_log[-10:]],
    }

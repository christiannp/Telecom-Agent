"""Telemetry Service for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from models import (
    UETelemetry,
    Subscriber,
    KPIState,
    QoSClass,
)
from config import SIMULATION_DENSITY


# ── Global State ─────────────────────────────────────────────────────────────
_latest_telemetry: List[UETelemetry] = []
_telemetry_history: List[UETelemetry] = []  # rolling window
_subscribers: Dict[str, Subscriber] = {}
_kpi_state = KPIState(timestamp=datetime.now())
_tick = 0
_MAX_HISTORY = 200


def update_telemetry(telemetry_batch: List[UETelemetry]) -> None:
    """Update global state with new telemetry batch."""
    global _latest_telemetry, _telemetry_history, _kpi_state, _tick, _subscribers

    _tick += 1
    _latest_telemetry = telemetry_batch

    # Extend history
    _telemetry_history.extend(telemetry_batch)
    if len(_telemetry_history) > _MAX_HISTORY:
        _telemetry_history = _telemetry_history[-_MAX_HISTORY:]

    # Update subscribers
    for te in telemetry_batch:
        if te.ue_id not in _subscribers:
            _subscribers[te.ue_id] = Subscriber(
                ue_id=te.ue_id,
                qos_class=te.qos_class,
                slice_type=te.slice_type,
                is_vip=(te.qos_class == QoSClass.VIP_PREMIUM),
            )

        sub = _subscribers[te.ue_id]
        sub.current_telemetry = te
        sub.rsrp_history.append(te.metrics.rsrp)
        sub.sinr_history.append(te.metrics.sinr)
        sub.ta_history.append(te.metrics.ta)

        # Keep last 60 entries
        if len(sub.rsrp_history) > 60:
            sub.rsrp_history = sub.rsrp_history[-60:]
        if len(sub.sinr_history) > 60:
            sub.sinr_history = sub.sinr_history[-60:]
        if len(sub.ta_history) > 60:
            sub.ta_history = sub.ta_history[-60:]

        if not te.metrics.handover_success:
            sub.handover_count += 1

        # Calculate frustration index
        _update_frustration(sub, te)

    # Update KPIs
    _kpi_state = _calculate_kpis(telemetry_batch, _tick)


def _update_frustration(sub: Subscriber, te: UETelemetry) -> None:
    """Update subscriber frustration index based on telemetry."""
    # High frustration: low RSRP + low SINR + high retransmission
    rsrp_factor = max(0, (te.metrics.rsrp + 120) / 30)  # -120dBm = 0, -90dBm = 1
    sinr_factor = max(0, te.metrics.sinr / 20)  # 20dB = 1, 0dB = 0
    retrans_factor = 1 - min(1.0, te.metrics.packet_retransmission_rate * 10)

    quality = (rsrp_factor * 0.4 + sinr_factor * 0.4 + retrans_factor * 0.2)
    sub.frustration_index = max(0, (1 - quality) * 100)


def _calculate_kpis(batch: List[UETelemetry], tick: int) -> KPIState:
    """Calculate executive KPIs from telemetry."""
    if not batch:
        return _kpi_state

    import statistics

    rsrp_vals = [t.metrics.rsrp for t in batch]
    sinr_vals = [t.metrics.sinr for t in batch]
    prb_vals = [t.metrics.prb_utilization for t in batch]

    avg_rsrp = statistics.mean(rsrp_vals)
    avg_sinr = statistics.mean(sinr_vals)
    avg_prb = statistics.mean(prb_vals)

    # VIP subscribers
    vip_batch = [t for t in batch if t.qos_class == QoSClass.VIP_PREMIUM]
    vip_rsrp = [t.metrics.rsrp for t in vip_batch] if vip_batch else [-90]
    vip_sinr = [t.metrics.sinr for t in vip_batch] if vip_batch else [15]

    # QoE calculation (0-100)
    vip_qoe = max(0, min(100,
        (max(0, (statistics.mean(vip_rsrp) + 120) / 30) * 50) +
        (max(0, statistics.mean(vip_sinr) / 20) * 50)
    ))

    # Satisfaction score
    sat_score = max(0, min(100,
        100 - (avg_prb / 2) - (max(0, 100 + avg_rsrp)) / 5
    ))

    # Congestion risk
    cong_risk = min(100.0, avg_prb * 1.1)

    # AI confidence (simulated, increases with more data)
    ai_conf = min(95.0, 60.0 + min(30, tick * 0.5))

    # Revenue protection (USD per event)
    revenue_protected = vip_qoe * 50  # Simulated

    # Mobility pressure (increases over time)
    mob_pressure = min(100.0, tick * 1.5)

    # SLA health
    sla_health = max(0, min(100, 100 - (100 - sat_score) * 0.5 - (100 - vip_qoe) * 0.5))

    return KPIState(
        timestamp=datetime.now(),
        subscriber_satisfaction_score=round(sat_score, 2),
        vip_qoe_score=round(vip_qoe, 2),
        congestion_risk=round(cong_risk, 2),
        ai_confidence=round(ai_conf, 2),
        sla_health=round(sla_health, 2),
        revenue_protection_usd=round(revenue_protected, 2),
        predicted_mobility_pressure=round(mob_pressure, 2),
        congestion_prevented=round(min(100, tick * 0.3), 2),
        estimated_sla_savings_usd=round(sat_score * 25, 2),
        ai_mitigation_success_rate=round(min(100, 70 + tick * 0.2), 2),
        vip_retention_risk_reduction=round(min(100, tick * 0.5), 2),
    )


def get_current_state() -> Dict:
    """Return full system state snapshot for the dashboard."""
    return {
        "kpis": _kpi_state,
        "active_ues": len(_latest_telemetry),
        "tick": _tick,
        "telemetry": _latest_telemetry,
        "subscribers": _subscribers,
        "history": _telemetry_history[-100:],
    }


def get_kpi_snapshot() -> KPIState:
    """Return current KPI state."""
    return _kpi_state


def get_subscriber_state(ue_id: str) -> Optional[Subscriber]:
    """Return individual subscriber state."""
    return _subscribers.get(ue_id)


def get_all_vip_subscribers() -> List[Subscriber]:
    """Return all VIP subscribers."""
    return [s for s in _subscribers.values() if s.is_vip]


def get_history(window: int = 60) -> List[UETelemetry]:
    """Return telemetry history window."""
    return _telemetry_history[-window:]
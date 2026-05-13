"""Telemetry Service for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from models import (
    UETelemetry,
    Subscriber,
    KPIState,
    QoSClass,
)
from config import SIMULATION_DENSITY

# ── Cross-process shared state ───────────────────────────────────────────────
# Written by the streamer process; read by the ADK web subprocess so it
# always sees the live simulation tick even when running in a separate process.
_SHARED_STATE_FILE = Path(__file__).parent.parent / "logs" / "_shared_state.json"
_SHARED_STATE_FILE.parent.mkdir(exist_ok=True)


def write_shared_state(
    tick: int,
    kpis: "KPIState",
    active_ues: int,
    status: str = "streaming",
) -> None:
    """Write current state to a JSON file readable by cross-process consumers."""
    try:
        _SHARED_STATE_FILE.write_text(
            json.dumps(
                {
                    "tick": tick,
                    "status": status,
                    "active_ues": active_ues,
                    "subscriber_satisfaction_score": kpis.subscriber_satisfaction_score,
                    "vip_qoe_score": kpis.vip_qoe_score,
                    "congestion_risk": kpis.congestion_risk,
                    "ai_confidence": kpis.ai_confidence,
                    "sla_health": kpis.sla_health,
                    "predicted_mobility_pressure": kpis.predicted_mobility_pressure,
                    "timestamp": datetime.now().isoformat(),
                },
                indent=2,
            )
        )
    except Exception:
        pass  # Non-critical — never crash the simulation over a stale file write


def read_shared_state() -> Dict:
    """Read the last state written by the streamer process."""
    try:
        if _SHARED_STATE_FILE.exists():
            return json.loads(_SHARED_STATE_FILE.read_text())
    except Exception:
        pass
    return {"tick": 0, "status": "idle", "active_ues": 0}


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

    # Cross-process sync: write live state so the ADK subprocess sees it
    write_shared_state(_tick, _kpi_state, len(telemetry_batch))


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
    """
    Return full system state snapshot for the dashboard and ADK tools.

    The tick is ALWAYS read from the shared state file so that the ADK web
    subprocess (which has its own copy of module globals) sees the live
    simulation tick rather than its own stale _tick=0.
    """
    shared = read_shared_state()
    live_tick = shared.get("tick", _tick)
    return {
        "kpis": _kpi_state,
        "active_ues": shared.get("active_ues", len(_latest_telemetry)),
        "tick": live_tick,
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


# ══════════════════════════════════════════════════════════════════════════════
# AGENTIC AI SKILLS LAYER
# ─────────────────────────────────────────────────────────────────────────────
# Implements:
#   1. Session Memory        — cross-turn context per agent
#   2. Incident Replay       — point-in-time snapshots + playback controls
#   3. Time-Series Analytics — rolling stats, anomaly detection, forecasting
# ══════════════════════════════════════════════════════════════════════════════

import uuid
import statistics as _stats
from dataclasses import dataclass, field

# ── Session Memory ──────────────────────────────────────────────────────────
_agent_memory: dict[str, list[dict]] = {}   # agent_name → list of reasoning entries
_reasoning_log: list[dict] = []             # global ordered log

MEMORY_MAX_ENTRIES = 50   # keep last N entries per agent


def store_agent_reasoning(
    agent_name: str,
    agent_type: str,
    reasoning: str,
    confidence: float = 75.0,
    triggered_action: str | None = None,
    color: str = "cyan",
) -> str:
    """
    Persist an agent's reasoning step to session memory.

    This is the core of the MEMORY skill — agents call this after each
    analysis cycle so the next turn has full contextual history.

    Returns the entry_id for later retrieval.
    """
    entry = {
        "entry_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        "agent_name": agent_name,
        "agent_type": agent_type,
        "reasoning": reasoning,
        "confidence": confidence,
        "triggered_action": triggered_action,
        "color": color,
    }

    # Per-agent memory
    if agent_name not in _agent_memory:
        _agent_memory[agent_name] = []
    _agent_memory[agent_name].append(entry)
    if len(_agent_memory[agent_name]) > MEMORY_MAX_ENTRIES:
        _agent_memory[agent_name] = _agent_memory[agent_name][-MEMORY_MAX_ENTRIES:]

    # Global reasoning log (last 200)
    _reasoning_log.append(entry)
    if len(_reasoning_log) > 200:
        _reasoning_log[:] = _reasoning_log[-200:]

    return entry["entry_id"]


def get_agent_memory(agent_name: str, limit: int = 10) -> list[dict]:
    """
    Retrieve the last N reasoning entries for a specific agent.

    This feeds the MEMORY skill so agents can reason with continuity
    across multiple turns.
    """
    mem = _agent_memory.get(agent_name, [])
    return mem[-limit:]


def get_reasoning_summary(limit: int = 20) -> list[dict]:
    """
    Return a global cross-agent reasoning summary for the orchestrator.
    Used by the Intent Orchestration Agent to maintain situational awareness.
    """
    return _reasoning_log[-limit:]


def clear_agent_memory(agent_name: str | None = None) -> str:
    """
    Clear memory for a specific agent, or all agents if agent_name is None.
    """
    if agent_name:
        _agent_memory.pop(agent_name, None)
        return f"Memory cleared for '{agent_name}'"
    _agent_memory.clear()
    _reasoning_log.clear()
    return "All agent memory cleared"


# ── Incident Replay ─────────────────────────────────────────────────────────
_replay_snapshots: list[dict] = []       # saved system snapshots
_replay_controller: dict = {
    "status": "stopped",
    "speed": 1.0,
    "current_tick": 0,
    "start_tick": 0,
    "end_tick": 0,
}


def save_replay_snapshot(reasoning_log: list[dict] | None = None) -> str:
    """
    Capture a point-in-time snapshot of the full system state.

    Called by the orchestrator after each analysis cycle so the operator
    can replay the incident later with full fidelity (telemetry + reasoning + actions).
    """
    global _replay_snapshots
    kpis = get_kpi_snapshot()
    telemetry = _latest_telemetry[-20:]  # sample

    snapshot = {
        "snapshot_id": str(uuid.uuid4())[:8],
        "tick": _tick,
        "timestamp": datetime.now().isoformat(),
        "active_ues": len(_latest_telemetry),
        "kpis": kpis.model_dump(),
        "telemetry_sample": [t.model_dump(mode="json") for t in telemetry],
        "reasoning_log": reasoning_log or [],
        "executed_actions": [],
    }

    _replay_snapshots.append(snapshot)
    # Keep last 120 snapshots (covers ~60s of simulation at 500ms tick)
    if len(_replay_snapshots) > 120:
        _replay_snapshots[:] = _replay_snapshots[-120:]
    return snapshot["snapshot_id"]


def get_replay_snapshots(start_tick: int | None = None, end_tick: int | None = None) -> list[dict]:
    """
    Return replay snapshots within a tick range.
    Used by the UI replay console.
    """
    snaps = _replay_snapshots
    if start_tick is not None:
        snaps = [s for s in snaps if s["tick"] >= start_tick]
    if end_tick is not None:
        snaps = [s for s in snaps if s["tick"] <= end_tick]
    return snaps


def set_replay_controller(
    status: str | None = None,
    speed: float | None = None,
    start_tick: int | None = None,
    end_tick: int | None = None,
    current_tick: int | None = None,
) -> dict:
    """
    Control the replay playback state.
    Supports: play, pause, stop, speed (0.5x, 1x, 2x, 5x, 10x), seek.
    """
    global _replay_controller
    if status is not None:
        _replay_controller["status"] = status
    if speed is not None:
        _replay_controller["speed"] = speed
    if start_tick is not None:
        _replay_controller["start_tick"] = start_tick
    if end_tick is not None:
        _replay_controller["end_tick"] = end_tick
    if current_tick is not None:
        _replay_controller["current_tick"] = current_tick
    return dict(_replay_controller)


def get_replay_controller() -> dict:
    """Return current replay playback state."""
    return dict(_replay_controller)


# ── Time-Series Analytics ─────────────────────────────────────────────────────
def compute_time_series_stats(
    metric_name: str,
    window: int = 30,
) -> dict:
    """
    Compute rolling statistics for a named telemetry metric.

    Supported metric_names:
      - rsrp, sinr, ta, prb_utilization, throughput_mbps
      - handover_success_rate, packet_retransmission_rate

    Implements the full TIME-SERIES ANALYTICS skill:
      - Rolling mean / std / min / max
      - Trend detection (rising / falling / stable)
      - Anomaly detection (values > 2σ from mean)
      - Simple linear forecast of next value
    """
    metric_map = {
        "rsrp":            lambda t: t.metrics.rsrp,
        "sinr":            lambda t: t.metrics.sinr,
        "ta":              lambda t: t.metrics.ta,
        "prb_utilization": lambda t: t.metrics.prb_utilization,
        "throughput_mbps": lambda t: t.metrics.throughput_mbps,
        "cqi":             lambda t: t.metrics.cqi,
    }

    extractor = metric_map.get(metric_name)
    if extractor is None:
        raise ValueError(
            f"Unknown metric '{metric_name}'. "
            f"Supported: {list(metric_map.keys())}"
        )

    # Use rolling window of telemetry history
    history = _telemetry_history[-window:]
    if not history:
        return {"error": "No telemetry history available"}

    values = [extractor(t) for t in history]
    current = values[-1]
    mean = _stats.mean(values)
    std  = _stats.stdev(values) if len(values) > 1 else 0.0

    # Trend: compare first half vs second half of window
    mid = len(values) // 2
    first_half = values[:mid] if mid > 0 else values
    second_half = values[mid:] if mid > 0 else values
    first_mean = _stats.mean(first_half)
    second_mean = _stats.mean(second_half)
    trend_pct = ((second_mean - first_mean) / abs(first_mean) * 100) if first_mean != 0 else 0.0
    trend_dir = (
        "rising" if trend_pct > 5
        else "falling" if trend_pct < -5
        else "stable"
    )

    # Anomaly: any value > 2σ from mean
    anomaly = any(abs(v - mean) > 2 * std for v in values) if std > 0 else False
    anomaly_reason = None
    if anomaly:
        outliers = [v for v in values if abs(v - mean) > 2 * std]
        anomaly_reason = f"Outliers detected: {[round(v, 2) for v in outliers]}"

    # Simple linear forecast (next value)
    if len(values) >= 2 and std > 0:
        # weighted slope toward recent values
        weights = list(range(1, len(values) + 1))
        w_mean  = sum(w * v for w, v in zip(weights, values)) / sum(weights)
        w_var   = sum(w * (v - w_mean) ** 2 for w, v in zip(weights, values)) / sum(weights)
        w_std   = w_var ** 0.5
        forecast = values[-1] + (w_mean - values[-1]) / len(values) if w_std > 0 else values[-1]
    else:
        forecast = current

    # Confidence interval (95%)
    ci_half = 1.96 * std if std > 0 else 0.0

    return {
        "metric_name": metric_name,
        "window_size": len(values),
        "current": round(current, 3),
        "mean": round(mean, 3),
        "std_dev": round(std, 3),
        "min_val": round(min(values), 3),
        "max_val": round(max(values), 3),
        "trend_direction": trend_dir,
        "trend_pct": round(trend_pct, 2),
        "anomaly_detected": anomaly,
        "anomaly_reason": anomaly_reason,
        "forecast_next": round(forecast, 3),
        "confidence_interval": (round(current - ci_half, 3), round(current + ci_half, 3)),
        "data_points": [round(v, 2) for v in values[-20:]],
    }


def detect_anomalies(window: int = 30) -> list[dict]:
    """
    Run anomaly detection across all primary metrics simultaneously.
    Returns a list of detected anomalies with severity assessment.
    """
    metrics = ["rsrp", "sinr", "ta", "prb_utilization", "throughput_mbps"]
    anomalies = []
    for metric in metrics:
        try:
            stats = compute_time_series_stats(metric, window)
            if stats.get("anomaly_detected"):
                # Severity based on how far out of band
                val = stats["current"]
                mean = stats["mean"]
                std  = stats["std_dev"]
                sigma = abs(val - mean) / std if std > 0 else 0
                if sigma > 3:
                    severity = "RED"
                elif sigma > 2:
                    severity = "ORANGE"
                else:
                    severity = "YELLOW"
                anomalies.append({
                    "metric": metric,
                    "severity": severity,
                    "sigma": round(sigma, 2),
                    "current": val,
                    "expected_range": stats["confidence_interval"],
                    "reason": stats["anomaly_reason"],
                    "trend": stats["trend_direction"],
                })
        except Exception:
            pass
    return anomalies


# ── Continuous Monitoring ──────────────────────────────────────────────────────
_monitoring_states: dict[str, dict] = {}  # agent_name → monitoring state


def start_monitoring(agent_name: str) -> dict:
    """Activate continuous monitoring loop for an agent."""
    _monitoring_states[agent_name] = {
        "monitoring_active": True,
        "last_monitored_tick": _tick,
        "alert_count": 0,
        "last_alert_type": None,
        "last_alert_severity": None,
        "consecutive_checks": 0,
        "escalation_level": 0,
        "started_at": datetime.now().isoformat(),
    }
    return _monitoring_states[agent_name]


def check_monitoring(agent_name: str, alert_type: str | None = None, severity: str = "YELLOW") -> dict:
    """
    Run a monitoring check for an agent.
    Tracks consecutive checks and escalates if conditions persist.
    Escalation levels: 0=normal, 1=watch, 2=warning, 3=critical
    """
    state = _monitoring_states.get(agent_name)
    if not state or not state.get("monitoring_active"):
        return {"status": "not_monitoring", "agent": agent_name}

    state["last_monitored_tick"] = _tick
    state["consecutive_checks"] += 1

    if alert_type:
        state["last_alert_type"] = alert_type
        state["last_alert_severity"] = severity
        state["alert_count"] += 1

    # Escalation: after 3 consecutive alerts, escalate one level
    if alert_type and state["consecutive_checks"] >= 3:
        severity_map = {"YELLOW": 1, "ORANGE": 2, "RED": 3}
        lvl = severity_map.get(severity, 1)
        state["escalation_level"] = min(3, lvl + state["escalation_level"])

    return {
        "agent": agent_name,
        "escalation_level": state["escalation_level"],
        "escalation_label": ["NOMINAL", "WATCH", "WARNING", "CRITICAL"][state["escalation_level"]],
        "consecutive_checks": state["consecutive_checks"],
        "alert_count": state["alert_count"],
        "last_alert_type": state.get("last_alert_type"),
        "tick": _tick,
    }


def stop_monitoring(agent_name: str) -> dict:
    """Deactivate monitoring for an agent."""
    if agent_name in _monitoring_states:
        _monitoring_states[agent_name]["monitoring_active"] = False
    return {"agent": agent_name, "monitoring_active": False}


def get_monitoring_state(agent_name: str | None = None) -> dict:
    """Return monitoring state for one agent or all agents."""
    if agent_name:
        return _monitoring_states.get(agent_name, {"status": "not_found"})
    return _monitoring_states
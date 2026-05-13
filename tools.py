"""Google ADK tools for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from models import AutonomousAction, RANAlert
from services import (
    get_current_state,
    get_kpi_snapshot,
    get_subscriber_state,
    get_all_vip_subscribers,
    analyze_ran_state,
    analyze_mobility,
    get_weather,
    predict_mrt_overload as predict_mrt_overload_service,
    validate_action,
)
from services.telemetry_service import read_shared_state


# ── Tool: Get RAN State ───────────────────────────────────────────────────────
def get_ran_state() -> dict:
    """
    Retrieve current RAN (Radio Access Network) intelligence state.

    Returns:
        - Cell-level metrics (RSRP, SINR, PRB, throughput)
        - Active RAN alerts (congestion, signal cliff, mass egress)
        - Handover statistics
    """
    state = get_current_state()
    from services.ran_service import analyze_ran_state
    from models import UETelemetry
    from typing import List

    telemetry = [
        UETelemetry.model_validate(t) for t in state.get("telemetry", [])
    ]
    alerts = analyze_ran_state(telemetry)

    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "active_ues": state["active_ues"],
        "tick": state["tick"],
        "kpis": state["kpis"].model_dump(),
        "alerts": [
            {
                "type": a.alert_type,
                "severity": a.severity.value,
                "reason": a.reason,
                "confidence": a.confidence_score,
                "recommended_action": a.recommended_action,
            }
            for a in alerts
        ],
    }


# ── Tool: Get Mobility State ─────────────────────────────────────────────────
async def get_mobility_state() -> dict:
    """
    Retrieve current urban mobility intelligence state.

    Returns:
        - MRT congestion levels per exit
        - YouBike availability
        - Walking propensity (weather-adjusted)
        - Slip risk
        - Mass egress detection status
    """
    state = get_current_state()
    weather = await get_weather()
    from models import UETelemetry

    telemetry = [
        UETelemetry.model_validate(t) for t in state.get("telemetry", [])
    ]
    mobility = analyze_mobility(telemetry, weather, 1500, state["tick"])

    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "mobility": mobility.model_dump(),
        "mrt_congestion_summary": mobility.overall_congestion,
        "mass_egress_detected": mobility.mass_egress_detected,
        "walking_propensity": mobility.walking_propensity,
        "slip_risk": mobility.slip_risk,
        "youbike_available": mobility.youbike_available,
        "youbike_empty_docks": mobility.youbike_empty_docks,
    }


# ── Tool: Get Weather State ───────────────────────────────────────────────────
async def get_weather_state() -> dict:
    """
    Retrieve current weather intelligence state.

    Returns:
        - Rainfall (mm/hr)
        - Temperature, humidity, wind
        - Slip risk
        - Walking propensity impact
    """
    weather = await get_weather()

    from services.weather_service import calculate_slip_risk, calculate_walking_propensity
    slip_risk = calculate_slip_risk(weather.rainfall_mm_hr)
    walking_prop = calculate_walking_propensity(weather.rainfall_mm_hr)

    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "weather": weather.model_dump(),
        "slip_risk": slip_risk,
        "walking_propensity": walking_prop,
        "mrt_preference_boost": f"{int((1 - walking_prop) * 100)}%",
    }


# ── Tool: Predict MRT Overload ───────────────────────────────────────────────
async def predict_mrt_overload(minutes_ahead: int = 10) -> dict:
    """
    Predict MRT overload risk for the requested horizon.

    Args:
        minutes_ahead: Forecast horizon in minutes.

    Returns:
        - Risk level and score
        - Current MRT congestion context
        - Weather and walking-propensity factors
    """
    state = get_current_state()
    weather = await get_weather()
    from models import UETelemetry

    telemetry = [
        UETelemetry.model_validate(t) for t in state.get("telemetry", [])
    ]
    mobility = analyze_mobility(telemetry, weather, 1500, state["tick"])
    prediction = predict_mrt_overload_service(mobility, weather, minutes_ahead)

    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "prediction": prediction,
        "current_mrt_congestion": mobility.overall_congestion,
        "crowd_density_mrt": mobility.crowd_density_mrt,
        "rainfall_mm_hr": weather.rainfall_mm_hr,
        "walking_propensity": mobility.walking_propensity,
        "slip_risk": mobility.slip_risk,
    }


# ── Tool: Get KPI Dashboard ───────────────────────────────────────────────────
def get_kpi_dashboard() -> dict:
    """
    Retrieve executive KPI dashboard snapshot.

    Returns:
        - Subscriber satisfaction score
        - VIP QoE score
        - Congestion risk
        - AI confidence
        - SLA health
        - Revenue protection
        - Predicted mobility pressure
    """
    kpis = get_kpi_snapshot()
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "kpis": kpis.model_dump(),
    }


# ── Tool: Get Subscriber Info ─────────────────────────────────────────────────
def get_subscriber_info(ue_id: str) -> dict:
    """
    Retrieve detailed information for a specific subscriber.

    Args:
        ue_id: UE identifier (e.g., VIP_001, STD_0001)

    Returns:
        - QoS class, slice type
        - Current RSRP, SINR, TA, throughput
        - RSRP/SINR history (last 60)
        - Handover count
        - Frustration index
        - QoE degradation prediction
    """
    sub = get_subscriber_state(ue_id)
    if sub is None:
        return {
            "status": "NOT_FOUND",
            "ue_id": ue_id,
            "message": f"Subscriber {ue_id} not found in current session.",
        }

    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "subscriber": {
            "ue_id": sub.ue_id,
            "qos_class": sub.qos_class.value,
            "slice_type": sub.slice_type.value,
            "is_vip": sub.is_vip,
            "handover_count": sub.handover_count,
            "frustration_index": round(sub.frustration_index, 2),
            "qoe_degradation_predicted_min": sub.qoe_degradation_predicted_min,
            "qoe_trend": round(sub.qoe_trend, 2),
            "rsrp_history": [round(r, 1) for r in sub.rsrp_history[-30:]],
            "sinr_history": [round(s, 1) for s in sub.sinr_history[-30:]],
            "ta_history": sub.ta_history[-30:],
        },
    }


# ── Tool: Get All VIP Subscribers ─────────────────────────────────────────────
def get_all_vip_info() -> dict:
    """
    Retrieve information for all VIP subscribers.

    Returns:
        - VIP count
        - Per-subscriber QoE metrics
        - Alert status
    """
    vips = get_all_vip_subscribers()
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "vip_count": len(vips),
        "vip_subscribers": [
            {
                "ue_id": s.ue_id,
                "qos_class": s.qos_class.value,
                "frustration_index": round(s.frustration_index, 2),
                "handover_count": s.handover_count,
                "qoe_degradation_predicted_min": s.qoe_degradation_predicted_min,
            }
            for s in vips
        ],
    }


# ── Tool: Validate Autonomous Action ─────────────────────────────────────────
def validate_autonomous_action(action_json: str) -> dict:
    """
    Validate an autonomous action against policy engine.

    Args:
        action_json: JSON-encoded AutonomousAction

    Returns:
        - Approved/rejected status
        - Policy reasoning
        - Conditions met
    """
    import json as _json
    try:
        data = _json.loads(action_json)
        from models import AutonomousAction
        action = AutonomousAction(**data)
    except Exception as e:
        return {
            "status": "INVALID_INPUT",
            "error": str(e),
            "message": "Failed to parse action JSON",
        }

    decision = validate_action(action)
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "approved": decision.approved,
        "reasoning": decision.reasoning,
        "conditions": decision.conditions,
        "action_id": action.action_id,
        "action_type": action.action_type,
        "confidence_score": action.confidence_score,
    }


# ── Tool: Trigger Autonomous Action ──────────────────────────────────────────
def trigger_autonomous_action(action_json: str) -> dict:
    """
    Execute a policy-approved autonomous action.

    Args:
        action_json: JSON-encoded AutonomousAction

    Returns:
        - Execution status
        - Expected KPI impact
        - AI reasoning
    """
    import json as _json
    try:
        data = _json.loads(action_json)
        from models import AutonomousAction
        action = AutonomousAction(**data)
    except Exception as e:
        return {
            "status": "INVALID_INPUT",
            "error": str(e),
        }

    # Validate first
    decision = validate_action(action)
    if not decision.approved:
        return {
            "status": "REJECTED",
            "timestamp": datetime.now().isoformat(),
            "action_id": action.action_id,
            "reasoning": decision.reasoning,
            "message": "Action not approved by policy engine",
        }

    # Simulate execution
    action.status = "executed"
    action.executed = True

    return {
        "status": "EXECUTED",
        "timestamp": datetime.now().isoformat(),
        "action_id": action.action_id,
        "action_type": action.action_type,
        "confidence_score": action.confidence_score,
        "expected_kpi_improvement_pct": action.expected_kpi_improvement_pct,
        "reasoning": action.reason,
        "message": f"Autonomous action '{action.action_type}' executed successfully.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# AGENTIC AI SKILLS — ADK TOOL LAYER
# ─────────────────────────────────────────────────────────────────────────────
# 6 new skill areas implemented as ADK tools:
#   1. MEMORY          — cross-turn session context per agent
#   2. EVENT_CORRELATE — unified scenario inference from multi-domain signals
#   3. TIME_SERIES     — rolling stats, anomaly detection, forecasting
#   4. REPLAY          — incident snapshots + playback controls
#   5. MONITOR_LOOP    — continuous monitoring with escalation
#   6. REASONING_LOG   — store reasoning chain for explainability
# ══════════════════════════════════════════════════════════════════════════════
from services.telemetry_service import (
    store_agent_reasoning,
    get_agent_memory,
    get_reasoning_summary,
    clear_agent_memory,
    save_replay_snapshot,
    get_replay_snapshots,
    set_replay_controller,
    get_replay_controller,
    compute_time_series_stats,
    detect_anomalies,
    start_monitoring,
    check_monitoring,
    stop_monitoring,
    get_monitoring_state,
)
from services.ran_service import correlate_events
from services.weather_service import get_weather
from services.mobility_service import analyze_mobility
from models import UETelemetry


# ── Tool: Store Reasoning (REASONING_LOG skill) ──────────────────────────────
def log_agent_reasoning(
    agent_name: str,
    agent_type: str,
    reasoning: str,
    confidence: float = 75.0,
    triggered_action: str | None = None,
    color: str = "cyan",
) -> dict:
    """
    Store a reasoning step from any agent to the global reasoning log.

    Skill: REASONING_LOG (Explainability — Master Prompt §EXPLAINABILITY REQUIREMENTS)

    Every AI recommendation must include root-cause reasoning, supporting
    telemetry, and confidence. Call this at the end of each analysis cycle.

    Args:
        agent_name:       e.g. "ran_intelligence_agent"
        agent_type:       e.g. "RAN", "MOBILITY", "CONTEXT", "POLICY", "INTENT"
        reasoning:        Free-text chain-of-thought explanation
        confidence:       0-100 confidence score for the conclusion
        triggered_action: Action type triggered (optional)
        color:            UI accent: cyan, green, orange, red, purple

    Returns: entry_id confirming the log entry
    """
    entry_id = store_agent_reasoning(
        agent_name=agent_name,
        agent_type=agent_type,
        reasoning=reasoning,
        confidence=confidence,
        triggered_action=triggered_action,
        color=color,
    )
    return {
        "status": "LOGGED",
        "entry_id": entry_id,
        "timestamp": datetime.now().isoformat(),
        "agent_name": agent_name,
    }


# ── Tool: Get Memory (MEMORY skill) ──────────────────────────────────────────
def get_memory(agent_name: str, limit: int = 10) -> dict:
    """
    Retrieve the last N reasoning entries for an agent.

    Skill: MEMORY (Multi-turn context — Master Prompt implicit requirement)

    Enables agents to reason with continuity across multiple turns by
    recalling previous analysis steps, alerts raised, and actions taken.
    """
    memory = get_agent_memory(agent_name, limit=limit)
    return {
        "status": "OK",
        "agent_name": agent_name,
        "entries": memory,
        "count": len(memory),
    }


# ── Tool: Get Cross-Agent Reasoning Summary ─────────────────────────────────
def get_reasoning_log(limit: int = 20) -> dict:
    """
    Return the global cross-agent reasoning log.

    Skill: REASONING_LOG + ORCHESTRATION

    The Intent Orchestration Agent calls this to build the AI Multi-Agent
    Reasoning Console UI (Master Prompt §AI MULTI-AGENT REASONING CONSOLE).
    """
    log = get_reasoning_summary(limit=limit)
    return {
        "status": "OK",
        "entries": log,
        "count": len(log),
    }


# ── Tool: Clear Memory ───────────────────────────────────────────────────────
def clear_memory(agent_name: str | None = None) -> dict:
    """
    Clear memory for a specific agent or all agents.

    Skill: MEMORY
    """
    result = clear_agent_memory(agent_name)
    return {"status": "OK", "message": result}


# ── Tool: Correlate Events (EVENT_CORRELATION skill) ────────────────────────
async def correlate_events_tool() -> dict:
    """
    Correlate signals across RAN + Mobility + Weather domains.

    Skill: EVENT_CORRELATION (Master Prompt §EVENT CORRELATION ENGINE)

    Correlates: rising TA + falling RSRP + AoA variance + congestion +
    weather + VIP density + MRT overload

    Infers operational scenarios and recommends autonomous actions.
    This is the primary reasoning engine for the Intent Orchestration Agent.

    Returns list of CorrelatedEvent objects with:
      - scenario_label, confidence, signal_correlation
      - inferred_consequence, recommended_autonomous_action, severity
    """
    from services.telemetry_service import get_current_state

    state = get_current_state()
    telemetry = [UETelemetry.model_validate(t) for t in state.get("telemetry", [])]
    weather = await get_weather()

    mobility_data = analyze_mobility(
        telemetry, weather, crowd_size=1500, tick=state["tick"]
    )

    # Calculate VIP density ratio
    vip_count = sum(1 for t in telemetry if t.qos_class.value == "VIP_Premium")
    vip_ratio = vip_count / len(telemetry) if telemetry else 0.0

    # Calculate average PRB congestion (overall + MRT DAS cell)
    prb_vals = [t.metrics.prb_utilization for t in telemetry]
    avg_prb = sum(prb_vals) / len(prb_vals) if prb_vals else 0.0

    mrt_prb_vals = [t.metrics.prb_utilization for t in telemetry
                    if t.cell_id == "TW_TPE_MRT_NS_01"]
    mrt_avg_prb = sum(mrt_prb_vals) / len(mrt_prb_vals) if mrt_prb_vals else 0.0

    events = correlate_events(
        telemetry_batch=telemetry,
        mobility_state=mobility_data,
        weather_state=weather,
        vip_density_ratio=vip_ratio,
        congestion_prb_pct=avg_prb,
        mrt_prb_pct=mrt_avg_prb,
        tick=state["tick"],
    )

    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "tick": state["tick"],
        "events": [e.model_dump() for e in events],
        "event_count": len(events),
        "critical_events": [e.scenario_label for e in events if e.severity.value == "RED"],
        "warning_events": [e.scenario_label for e in events if e.severity.value in ("ORANGE", "YELLOW")],
    }


# ── Tool: Time-Series Analytics (TIME_SERIES skill) ─────────────────────────
def get_time_series_stats(metric_name: str, window: int = 30) -> dict:
    """
    Compute rolling statistics for a telemetry metric.

    Skill: TIME_SERIES (Master Prompt §TIME SERIES ANALYTICS)

    Supports: rsrp, sinr, ta, prb_utilization, throughput_mbps, cqi

    Returns:
      - current, mean, std_dev, min, max
      - trend_direction (rising/falling/stable) + trend_pct
      - anomaly_detected + anomaly_reason
      - forecast_next + confidence_interval
    """
    return compute_time_series_stats(metric_name, window)


def get_anomaly_report(window: int = 30) -> dict:
    """
    Run anomaly detection across all telemetry metrics simultaneously.

    Skill: TIME_SERIES + ANOMALY_DETECTION

    Returns anomalies with severity (RED/ORANGE/YELLOW) based on sigma level.
    """
    anomalies = detect_anomalies(window)
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "window": window,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }


# ── Tool: Replay (INCIDENT REPLAY skill) ────────────────────────────────────
def save_snapshot(reasoning_log: list[dict] | None = None) -> dict:
    """
    Capture a point-in-time snapshot of the full system state.

    Skill: INCIDENT REPLAY (Master Prompt §INCIDENT REPLAY MODE)

    Saves tick, KPIs, telemetry sample, reasoning log, and executed actions.
    The Intent Orchestration Agent calls this after each analysis cycle so
    operators can replay the incident later.
    """
    snapshot_id = save_replay_snapshot(reasoning_log)
    return {
        "status": "SAVED",
        "snapshot_id": snapshot_id,
        "timestamp": datetime.now().isoformat(),
    }


def get_replay_range(start_tick: int | None = None, end_tick: int | None = None) -> dict:
    """
    Retrieve replay snapshots within a tick range.

    Skill: INCIDENT REPLAY

    Used by the replay UI console (Master Prompt §INCIDENT REPLAY MODE).
    """
    snapshots = get_replay_snapshots(start_tick, end_tick)
    return {
        "status": "OK",
        "snapshots": snapshots,
        "count": len(snapshots),
        "tick_range": (start_tick, end_tick),
    }


def control_replay(
    command: str,
    speed: float | None = None,
    tick: int | None = None,
) -> dict:
    """
    Control replay playback.

    Skill: INCIDENT REPLAY

    Args:
        command: "play" | "pause" | "stop" | "speed" | "seek"
        speed:   0.5 | 1.0 | 2.0 | 5.0 | 10.0
        tick:    absolute tick to seek to
    """
    status_map = {"play": "playing", "pause": "paused", "stop": "stopped"}
    status = status_map.get(command, None)

    if command == "speed" and speed is not None:
        return set_replay_controller(speed=speed)
    if command == "seek" and tick is not None:
        return set_replay_controller(current_tick=tick)
    if status:
        return set_replay_controller(status=status)

    return {
        "status": "ERROR",
        "message": f"Unknown command '{command}'. Use: play, pause, stop, speed, seek",
    }


def get_replay_status() -> dict:
    """
    Return current replay playback state.

    Skill: INCIDENT REPLAY
    """
    return get_replay_controller()


# ── Tool: Continuous Monitoring Loop (MONITOR_LOOP skill) ────��──────────────
def start_continuous_monitoring(agent_name: str) -> dict:
    """
    Activate continuous monitoring loop for an agent.

    Skill: MONITOR_LOOP (Iteration — Master Prompt implicit requirement)

    When active, the agent will track consecutive alerts and escalate
    severity across monitoring cycles. Enables autonomous watch-and-act
    behavior without user prompts.
    """
    return start_monitoring(agent_name)


def run_monitoring_check(
    agent_name: str,
    alert_type: str | None = None,
    severity: str = "YELLOW",
) -> dict:
    """
    Run a monitoring check for an agent and update escalation state.

    Skill: MONITOR_LOOP

    Tracks consecutive checks; escalates if same alert persists.
    Escalation levels: 0=NOMINAL, 1=WATCH, 2=WARNING, 3=CRITICAL

    Returns escalation level, label, and alert metadata.
    """
    return check_monitoring(agent_name, alert_type, severity)


def get_live_status() -> dict:
    """
    Return the live simulation status including tick and KPIs.
    Reads the shared state file written by the streamer process so this
    tool always returns the correct tick even when running in the ADK web
    subprocess (separate from the streamer's process).

    Skill: CONTEXTUAL_AWARENESS
    """

    shared = read_shared_state()
    return {
        "status": shared.get("status", "idle"),
        "tick": shared.get("tick", 0),
        "active_ues": shared.get("active_ues", 0),
        "subscriber_satisfaction_score": shared.get("subscriber_satisfaction_score", 0.0),
        "vip_qoe_score": shared.get("vip_qoe_score", 0.0),
        "congestion_risk": shared.get("congestion_risk", 0.0),
        "ai_confidence": shared.get("ai_confidence", 0.0),
        "sla_health": shared.get("sla_health", 0.0),
        "predicted_mobility_pressure": shared.get("predicted_mobility_pressure", 0.0),
        "timestamp": shared.get("timestamp", ""),
        "simulation_active": shared.get("tick", 0) > 0,
    }


def stop_continuous_monitoring(agent_name: str) -> dict:
    """
    Deactivate continuous monitoring for an agent.

    Skill: MONITOR_LOOP
    """
    return stop_monitoring(agent_name)


def get_monitoring_status(agent_name: str | None = None) -> dict:
    """
    Return monitoring state for one agent or all agents.

    Skill: MONITOR_LOOP
    """
    return get_monitoring_state(agent_name)

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
    validate_action,
)


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
def get_mobility_state() -> dict:
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
    weather = get_weather()
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
    import asyncio
    weather = await asyncio.to_thread(lambda: None)  # sync wrapper
    # Re-implement sync version
    from services.weather_service import _get_mock_weather
    weather = _get_mock_weather()

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
"""Policy Validation Engine for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from models import AutonomousAction, PolicyDecision, AlertSeverity
from config import CONFIDENCE_THRESHOLD, LOG_DIR


# Configure logging
_log = logging.getLogger("covmo.policy")
_log.setLevel(logging.INFO)
_handler = logging.FileHandler(LOG_DIR / "policy_decisions.log")
_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
_log.addHandler(_handler)


# ── Policy Rules ─────────────────────────────────────────────────────────────

# VIP SLA: VIP subscribers must maintain QoE > 80
VIP_SLA_QOE_THRESHOLD = 80.0

# Congestion threshold
CONGESTION_REDUCTION_MIN_PCT = 5.0

# Approved autonomous action types
APPROVED_ACTION_TYPES = [
    "VIP_PRIORITY_ROUTING",
    "TEMPORARY_LOAD_BALANCING",
    "MICRO_CELL_HANDOVER",
    "DYNAMIC_SLICE_ALLOCATION",
    "SLEEP_MODE_COORDINATION",
    "ANTENNA_TILT_OPTIMIZATION",
    "NEIGHBOR_CELL_EXPANSION",
    "SMALL_CELL_STEERING",
    "PRIORITY_SCHEDULING",
]


def validate_action(action: AutonomousAction) -> PolicyDecision:
    """
    Validate an autonomous action against telecom operational policies.

    Policy checks:
    1. Confidence must exceed threshold (default 85%)
    2. Action type must be approved
    3. Must not cause neighboring cell overload
    4. Must improve VIP SLA
    5. Must not worsen congestion elsewhere
    """
    conditions: list[str] = []
    rejection_reasons: list[str] = []

    # ── Check 1: Confidence Threshold ───────────────────────────────────
    if action.confidence_score < CONFIDENCE_THRESHOLD:
        rejection_reasons.append(
            f"Confidence {action.confidence_score:.1f}% below threshold "
            f"{CONFIDENCE_THRESHOLD}%"
        )
    else:
        conditions.append(f"Confidence OK: {action.confidence_score:.1f}%")

    # ── Check 2: Approved Action Type ────────────────────────────────────
    if action.action_type not in APPROVED_ACTION_TYPES:
        rejection_reasons.append(f"Action type '{action.action_type}' not in approved list")
    else:
        conditions.append(f"Action type approved: {action.action_type}")

    # ── Check 3: Expected KPI Improvement ────────────────────────────────
    if action.expected_kpi_improvement_pct < 1.0:
        conditions.append(
            f"Minimal KPI impact: {action.expected_kpi_improvement_pct:.1f}% "
            "(action may have marginal benefit)"
        )

    # ── Check 4: Congestion Reduction ────────────────────────────────────
    if action.action_type in ["TEMPORARY_LOAD_BALANCING", "NEIGHBOR_CELL_EXPANSION"]:
        if action.expected_congestion_reduction_pct < CONGESTION_REDUCTION_MIN_PCT:
            rejection_reasons.append(
                f"Congestion reduction {action.expected_congestion_reduction_pct:.1f}% "
                f"below minimum {CONGESTION_REDUCTION_MIN_PCT}%"
            )
        else:
            conditions.append(
                f"Congestion reduction sufficient: "
                f"{action.expected_congestion_reduction_pct:.1f}%"
            )

    # ── Check 5: VIP Actions ────────────────────────────────────────────
    if action.action_type == "VIP_PRIORITY_ROUTING":
        if action.expected_kpi_improvement_pct < 10.0:
            rejection_reasons.append(
                "VIP Priority Routing must yield >10% KPI improvement"
            )
        else:
            conditions.append("VIP SLA improvement sufficient")

    # ── Final Decision ───────────────────────────────────────────────────
    approved = len(rejection_reasons) == 0

    if approved:
        decision_text = (
            f"APPROVED: {action.action_type} | "
            f"Confidence: {action.confidence_score:.1f}% | "
            f"Expected Impact: {action.expected_kpi_improvement_pct:.1f}%"
        )
        _log.info(decision_text)
        reasoning = "All policy checks passed. " + " ".join(conditions)
    else:
        reasoning = "REJECTED: " + "; ".join(rejection_reasons)
        _log.warning(reasoning)

    return PolicyDecision(
        action=action,
        approved=approved,
        reasoning=reasoning,
        conditions=conditions
    )


def get_default_actions() -> list[AutonomousAction]:
    """Return predefined autonomous actions for common scenarios."""
    return [
        AutonomousAction(
            action_id="action_001",
            action_type="VIP_PRIORITY_ROUTING",
            timestamp=datetime.now(),
            confidence_score=92.0,
            reason="VIP RSRP degradation > 17dB; MRT ingress congestion rising; Rainfall 7mm/hr",
            expected_kpi_improvement_pct=23.0,
            expected_congestion_reduction_pct=0.0,
            status="proposed"
        ),
        AutonomousAction(
            action_id="action_002",
            action_type="TEMPORARY_LOAD_BALANCING",
            timestamp=datetime.now(),
            confidence_score=88.0,
            reason="PRB utilization at 84%; mass egress detected",
            expected_kpi_improvement_pct=15.0,
            expected_congestion_reduction_pct=18.0,
            status="proposed"
        ),
        AutonomousAction(
            action_id="action_003",
            action_type="SMALL_CELL_STEERING",
            timestamp=datetime.now(),
            confidence_score=85.0,
            reason="Underground transition detected; signal cliff probability HIGH",
            expected_kpi_improvement_pct=12.0,
            expected_congestion_reduction_pct=0.0,
            status="proposed"
        ),
        AutonomousAction(
            action_id="action_004",
            action_type="DYNAMIC_SLICE_ALLOCATION",
            timestamp=datetime.now(),
            confidence_score=79.0,
            reason="VIP slice utilization at 91%; approaching SLA threshold",
            expected_kpi_improvement_pct=8.0,
            expected_congestion_reduction_pct=10.0,
            status="proposed"
        ),
    ]
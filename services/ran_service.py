"""RAN Intelligence Engine for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

import statistics
from datetime import datetime
from typing import List

from models import (
    UETelemetry,
    RANAlert,
    AlertSeverity,
    CellState,
)
from config import (
    CONGESTION_THRESHOLD_PRB,
    MASS_EGRESS_TA_PCT,
    SIGNAL_CLIFF_DB,
)


# ── RAN Physics Constants ───────────────────────────────────────────────────
TA_TO_METERS = 78.0  # LTE timing advance unit ≈ 78 meters
SPEED_OF_LIGHT = 299792458  # m/s
LTE_TS = 3.2552e-8  # LTE timing unit (seconds)


def calculate_distance_from_ta(ta: int) -> float:
    """
    Calculate distance from cell using Timing Advance.

    Distance ≈ TA × 78 meters (simplified)
    Distance = (c × (TA × Ts)) / 2 (precise)
    """
    return ta * TA_TO_METERS


def analyze_ran_state(telemetry_batch: List[UETelemetry]) -> List[RANAlert]:
    """
    Analyze RAN telemetry and generate alerts.

    Detects:
    - Mass egress (70%+ subscribers with increasing TA)
    - Signal cliffs (RSRP drop > 15dB, stable TA)
    - Multi-path interference (high AoA variance)
    - Congestion (PRB > 80%)
    - Handover failures
    """
    alerts: List[RANAlert] = []

    if not telemetry_batch:
        return alerts

    # ── Mass Egress Detection ───────────────────────────────────────────────
    ta_values = [t.metrics.ta for t in telemetry_batch]
    if len(ta_values) >= 5:
        # Check if TA is increasing (subscribers moving away from cell)
        ta_increasing_count = sum(
            1 for i in range(1, len(ta_values))
            if ta_values[i] > ta_values[i-1]
        )
        ta_increasing_pct = ta_increasing_count / len(ta_values)

        if ta_increasing_pct >= MASS_EGRESS_TA_PCT:
            alerts.append(RANAlert(
                timestamp=datetime.now(),
                alert_type="MASS_EGRESS_DETECTED",
                severity=AlertSeverity.ORANGE,
                reason=f"Mass egress pattern detected: {ta_increasing_pct*100:.1f}% of subscribers show increasing TA",
                supporting_telemetry={
                    "ta_increasing_pct": ta_increasing_pct,
                    "avg_ta": statistics.mean(ta_values),
                    "max_ta": max(ta_values),
                    "subscriber_count": len(telemetry_batch),
                },
                confidence_score=min(95.0, 70.0 + (ta_increasing_pct * 30)),
                recommended_action="Prepare for MRT ingress congestion; activate load balancing"
            ))

    # ── Signal Cliff Detection ──────────────────────────────────────────────
    for i in range(1, len(telemetry_batch)):
        prev = telemetry_batch[i-1]
        curr = telemetry_batch[i]

        if curr.ue_id == prev.ue_id:
            rsrp_drop = prev.metrics.rsrp - curr.metrics.rsrp
            ta_stable = abs(curr.metrics.ta - prev.metrics.ta) <= 2

            if rsrp_drop > SIGNAL_CLIFF_DB and ta_stable:
                alerts.append(RANAlert(
                    timestamp=datetime.now(),
                    alert_type="SIGNAL_CLIFF",
                    severity=AlertSeverity.RED,
                    cell_id=curr.cell_id,
                    reason=f"Signal cliff detected for UE {curr.ue_id}: RSRP drop {rsrp_drop:.1f}dB with stable TA",
                    supporting_telemetry={
                        "ue_id": curr.ue_id,
                        "rsrp_drop_db": rsrp_drop,
                        "prev_rsrp": prev.metrics.rsrp,
                        "curr_rsrp": curr.metrics.rsrp,
                        "ta_stable": ta_stable,
                    },
                    confidence_score=88.0,
                    recommended_action="Underground transition likely; steer to small-cell or DAS"
                ))

    # ── Multi-path Interference Detection ───────────────────────────────────
    aoa_values = [t.metrics.aoa for t in telemetry_batch]
    if len(aoa_values) >= 10:
        aoa_variance = statistics.variance(aoa_values)
        if aoa_variance > 1500:  # High variance indicates multi-path
            alerts.append(RANAlert(
                timestamp=datetime.now(),
                alert_type="MULTIPATH_INTERFERENCE",
                severity=AlertSeverity.YELLOW,
                reason=f"Multi-path interference detected: AoA variance {aoa_variance:.1f}°²",
                supporting_telemetry={
                    "aoa_variance": aoa_variance,
                    "aoa_mean": statistics.mean(aoa_values),
                    "aoa_stdev": statistics.stdev(aoa_values),
                },
                confidence_score=75.0,
                recommended_action="Arena architecture causing multi-path; consider micro-cell handover"
            ))

    # ── Congestion Detection ────────────────────────────────────────────────
    prb_values = [t.metrics.prb_utilization for t in telemetry_batch]
    avg_prb = statistics.mean(prb_values)

    if avg_prb > CONGESTION_THRESHOLD_PRB:
        severity = AlertSeverity.RED if avg_prb > 90 else AlertSeverity.ORANGE
        alerts.append(RANAlert(
            timestamp=datetime.now(),
            alert_type="CONGESTION_DETECTED",
            severity=severity,
            reason=f"Cell congestion detected: PRB utilization {avg_prb:.1f}%",
            supporting_telemetry={
                "avg_prb_utilization": avg_prb,
                "max_prb_utilization": max(prb_values),
                "active_ues": len(telemetry_batch),
            },
            confidence_score=92.0,
            recommended_action="Temporary load balancing to neighboring cells"
        ))

    # ── Handover Failure Prediction ─────────────────────────────────────────
    handover_failures = [t for t in telemetry_batch if not t.metrics.handover_success]
    if handover_failures:
        failure_rate = len(handover_failures) / len(telemetry_batch)
        if failure_rate > 0.05:  # > 5% failure rate
            alerts.append(RANAlert(
                timestamp=datetime.now(),
                alert_type="HANDOVER_FAILURE_RISK",
                severity=AlertSeverity.ORANGE,
                reason=f"Handover failure rate elevated: {failure_rate*100:.1f}%",
                supporting_telemetry={
                    "failure_rate": failure_rate,
                    "failed_handovers": len(handover_failures),
                    "total_handovers": len(telemetry_batch),
                },
                confidence_score=80.0,
                recommended_action="Review neighbor cell list; optimize handover parameters"
            ))

    return alerts


def calculate_cell_state(cell_id: str, telemetry_batch: List[UETelemetry]) -> CellState:
    """Calculate aggregated cell state from telemetry."""
    cell_telemetry = [t for t in telemetry_batch if t.cell_id == cell_id]

    if not cell_telemetry:
        return CellState(
            cell_id=cell_id,
            name=cell_id,
            lat=25.0516,
            lon=121.5500,
            cell_type="macro"
        )

    rsrp_values = [t.metrics.rsrp for t in cell_telemetry]
    sinr_values = [t.metrics.sinr for t in cell_telemetry]
    prb_values = [t.metrics.prb_utilization for t in cell_telemetry]
    throughput_values = [t.metrics.throughput_mbps for t in cell_telemetry]
    handover_success = [t.metrics.handover_success for t in cell_telemetry]

    return CellState(
        cell_id=cell_id,
        name=cell_id,
        lat=cell_telemetry[0].location.lat,
        lon=cell_telemetry[0].location.lon,
        cell_type="macro",
        active_ues=len(cell_telemetry),
        prb_utilization=statistics.mean(prb_values),
        avg_rsrp=statistics.mean(rsrp_values),
        avg_sinr=statistics.mean(sinr_values),
        handover_requests=len(cell_telemetry),
        handover_success_rate=(sum(handover_success) / len(handover_success) * 100) if handover_success else 100.0,
        throughput_mbps_avg=statistics.mean(throughput_values),
    )
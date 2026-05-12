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


# ══════════════════════════════════════════════════════════════════════════════
# EVENT CORRELATION ENGINE  (Master Prompt §EVENT CORRELATION ENGINE)
# ─────────────────────────────────────────────────────────────────────────────
# Correlates: rising TA + falling RSRP + AoA variance + congestion spikes
#           + weather + VIP density + MRT overload
# Infers operational scenarios and recommends autonomous actions.
# ══════════════════════════════════════════════════════════════════════════════
from datetime import datetime as _dt
from models import MobilityState, WeatherState, CorrelatedEvent, AlertSeverity
import uuid as _uuid


# Thresholds for correlation
_CORRELATION_THRESHOLDS = {
    "ta_increasing_pct": 0.65,     # 65% UEs with rising TA → mass egress
    "rsrp_degradation_db": 12.0,  # 12dB RSRP drop → signal cliff / underground
    "aoa_variance_threshold": 1200,  # AoA variance > 1200 → multi-path
    "prb_congestion_pct": 80.0,    # PRB > 80% → congestion
    "vip_density_threshold": 0.3,  # 30% VIPs in degraded area → VIP risk
    "mrt_pressure_threshold": 60,  # MRT pressure > 60 → overload concern
}


def correlate_events(
    telemetry_batch: list,
    mobility_state: MobilityState,
    weather_state: WeatherState,
    vip_density_ratio: float = 0.0,
    congestion_prb_pct: float = 0.0,
) -> list[CorrelatedEvent]:
    """
    Master Event Correlation Engine.

    Correlates signals across all intelligence domains to infer operational
    scenarios and return a list of CorrelatedEvent objects, each tagged with:
      - scenario label
      - confidence
      - signal correlation map
      - inferred consequence
      - recommended autonomous action

    This is the core reasoning skill that turns raw telemetry into
    actionable AI decisions. Called by the Intent Orchestration Agent
    after each analysis cycle.
    """
    events: list[CorrelatedEvent] = []
    now = _dt.now()

    if not telemetry_batch:
        return events

    # ── Extract signal vectors ────────────────────────────────────────────────
    ta_vals   = [t.metrics.ta for t in telemetry_batch]
    rsrp_vals = [t.metrics.rsrp for t in telemetry_batch]
    sinr_vals = [t.metrics.sinr for t in telemetry_batch]
    prb_vals  = [t.metrics.prb_utilization for t in telemetry_batch]
    aoa_vals  = [t.metrics.aoa for t in telemetry_batch]

    ta_rising_pct = _rising_pct(ta_vals) if len(ta_vals) >= 5 else 0.0

    # ── Scenario 1: MRT Underground Transition ──────────────────────────────
    # Signal pattern: falling RSRP + stable/low TA change + high VIP density
    # Inference: subscribers entering MRT underground — cell-edge degradation
    rsrp_falling = _avg_trend(rsrp_vals) < -0.5
    low_sinr_pct = sum(1 for s in sinr_vals if s < 8) / len(sinr_vals) if sinr_vals else 0

    if rsrp_falling and low_sinr_pct > 0.3:
        events.append(CorrelatedEvent(
            timestamp=now,
            event_id=f"evt_{_uuid.uuid4().hex[:8]}",
            scenario_label="MRT_UNDERGROUND_TRANSITION",
            agent_source="EventCorrelationEngine",
            confidence=min(95.0, 60.0 + low_sinr_pct * 35),
            signal_correlation={
                "avg_rsrp": round(statistics.mean(rsrp_vals), 1),
                "low_sinr_ratio": round(low_sinr_pct, 2),
                "vip_density_ratio": vip_density_ratio,
                "rainfall_mm_hr": weather_state.rainfall_mm_hr,
            },
            inferred_consequence=(
                "Subscribers entering MRT underground platform. "
                "Cell-edge RSRP degradation + SINR attenuation expected. "
                "Risk: VIP QoE degradation, handover failures at cell boundary."
            ),
            recommended_autonomous_action="SMALL_CELL_STEERING",
            severity=AlertSeverity.ORANGE,
            metadata={"cell_edge_rsrp": round(statistics.mean(rsrp_vals[-5:]), 1)},
        ))

    # ── Scenario 2: Mass Egress Confirmed ────────────────────────────────────
    # Signal pattern: TA rising + MRT congestion rising + weather impact
    if ta_rising_pct >= _CORRELATION_THRESHOLDS["ta_increasing_pct"]:
        events.append(CorrelatedEvent(
            timestamp=now,
            event_id=f"evt_{_uuid.uuid4().hex[:8]}",
            scenario_label="MASS_EGRESS_CONFIRMED",
            agent_source="EventCorrelationEngine",
            confidence=min(95.0, 70.0 + ta_rising_pct * 25),
            signal_correlation={
                "ta_rising_pct": round(ta_rising_pct, 3),
                "avg_ta": round(statistics.mean(ta_vals), 1),
                "mrt_pressure": mobility_state.crowd_pressure_propagation,
                "overall_congestion": mobility_state.overall_congestion,
                "rainfall": weather_state.rainfall_mm_hr,
                "egress_velocity_kmh": mobility_state.egress_velocity_kmh,
            },
            inferred_consequence=(
                f"Confirmed mass egress from Taipei Arena. "
                f"{round(ta_rising_pct * 100, 0):.0f}% of subscribers show increasing TA. "
                "MRT ingress congestion escalating. Weather intensifying MRT preference."
            ),
            recommended_autonomous_action="TEMPORARY_LOAD_BALANCING",
            severity=AlertSeverity.ORANGE,
            metadata={
                "active_ues": len(telemetry_batch),
                "egress_progress_pct": round(ta_rising_pct * 100, 1),
            },
        ))

    # ── Scenario 3: Multi-path Interference + Arena Architecture ──────────────
    # Signal pattern: high AoA variance + moderate SINR degradation
    if len(aoa_vals) >= 10:
        aoa_var = statistics.variance(aoa_vals)
        if aoa_var >= _CORRELATION_THRESHOLDS["aoa_variance_threshold"]:
            events.append(CorrelatedEvent(
                timestamp=now,
                event_id=f"evt_{_uuid.uuid4().hex[:8]}",
                scenario_label="MULTIPATH_ARENA_ARCHITECTURE",
                agent_source="EventCorrelationEngine",
                confidence=min(92.0, 50.0 + (aoa_var / 2000) * 40),
                signal_correlation={
                    "aoa_variance": round(aoa_var, 1),
                    "aoa_mean": round(statistics.mean(aoa_vals), 1),
                    "avg_sinr": round(statistics.mean(sinr_vals), 1),
                    "prb_congestion_pct": congestion_prb_pct,
                },
                inferred_consequence=(
                    "Multi-path interference detected. Likely caused by "
                    "Taipei Arena architecture (metal roof, reflective surfaces). "
                    "Signal quality degradation and retransmission rate elevation expected."
                ),
                recommended_autonomous_action="ANTENNA_TILT_OPTIMIZATION",
                severity=AlertSeverity.YELLOW,
                metadata={"aoa_stdev": round(statistics.stdev(aoa_vals), 1)},
            ))

    # ── Scenario 4: VIP QoE Risk / SLA Violation ─────────────────────────────
    # Signal pattern: VIP density + RSRP degradation + SINR low
    vip_rsrp_vals = [t.metrics.rsrp for t in telemetry_batch
                     if t.qos_class.value == "VIP_Premium"]
    if vip_rsrp_vals and vip_density_ratio >= _CORRELATION_THRESHOLDS["vip_density_threshold"]:
        vip_rsrp_avg = statistics.mean(vip_rsrp_vals)
        vip_sinr_avg = statistics.mean(
            t.metrics.sinr for t in telemetry_batch
            if t.qos_class.value == "VIP_Premium"
        )
        vip_qoe_estimate = _rsrp_to_qoe(vip_rsrp_avg, vip_sinr_avg)
        if vip_qoe_estimate < 80.0:
            events.append(CorrelatedEvent(
                timestamp=now,
                event_id=f"evt_{_uuid.uuid4().hex[:8]}",
                scenario_label="VIP_QOE_DEGRADATION_RISK",
                agent_source="EventCorrelationEngine",
                confidence=min(95.0, (80 - vip_qoe_estimate) * 2 + 50),
                signal_correlation={
                    "vip_count": len(vip_rsrp_vals),
                    "vip_rsrp_avg": round(vip_rsrp_avg, 1),
                    "vip_sinr_avg": round(vip_sinr_avg, 1),
                    "vip_qoe_estimate": round(vip_qoe_estimate, 1),
                    "sla_threshold": 80.0,
                    "degradation_db": round(-120 - vip_rsrp_avg, 1),
                },
                inferred_consequence=(
                    f"VIP SLA threshold at risk. Estimated VIP QoE: {vip_qoe_estimate:.0f}/100 "
                    f"(SLA threshold: 80). {len(vip_rsrp_vals)} VIP subscribers "
                    "experiencing degraded radio conditions."
                ),
                recommended_autonomous_action="VIP_PRIORITY_ROUTING",
                severity=AlertSeverity.RED,
                metadata={"qoe_delta_from_sla": round(80.0 - vip_qoe_estimate, 1)},
            ))

    # ── Scenario 5: Cell Congestion + PRB Saturation ────────────────────────
    if congestion_prb_pct >= _CORRELATION_THRESHOLDS["prb_congestion_pct"]:
        events.append(CorrelatedEvent(
            timestamp=now,
            event_id=f"evt_{_uuid.uuid4().hex[:8]}",
            scenario_label="PRB_CELL_CONGESTION",
            agent_source="EventCorrelationEngine",
            confidence=min(95.0, 60.0 + (congestion_prb_pct - 80) * 2),
            signal_correlation={
                "avg_prb_pct": round(congestion_prb_pct, 1),
                "max_prb": round(max(prb_vals), 1),
                "active_ues": len(telemetry_batch),
                "ta_rising_pct": round(ta_rising_pct, 3),
                "avg_sinr": round(statistics.mean(sinr_vals), 1),
            },
            inferred_consequence=(
                f"PRB utilization at {congestion_prb_pct:.0f}% — above congestion threshold. "
                f"Cell resource saturation reducing throughput for all subscribers. "
                "Autonomous load balancing recommended."
            ),
            recommended_autonomous_action="DYNAMIC_SLICE_ALLOCATION",
            severity=AlertSeverity.RED if congestion_prb_pct > 90 else AlertSeverity.ORANGE,
            metadata={"prb_headroom": round(100 - congestion_prb_pct, 1)},
        ))

    # ── Scenario 6: Signal Cliff / Underground Transition ───────────────────
    # Signal pattern: rapid RSRP drop + stable TA (not moving toward cell, just indoors)
    rsrp_drop = max(rsrp_vals) - min(rsrp_vals) if rsrp_vals else 0
    ta_range  = max(ta_vals) - min(ta_vals) if ta_vals else 0
    if rsrp_drop >= _CORRELATION_THRESHOLDS["rsrp_degradation_db"] and ta_range < 10:
        events.append(CorrelatedEvent(
            timestamp=now,
            event_id=f"evt_{_uuid.uuid4().hex[:8]}",
            scenario_label="SIGNAL_CLIFF_UNDERGROUND_TRANSITION",
            agent_source="EventCorrelationEngine",
            confidence=min(93.0, 50.0 + (rsrp_drop - 12) * 3),
            signal_correlation={
                "rsrp_drop_db": round(rsrp_drop, 1),
                "rsrp_max": round(max(rsrp_vals), 1),
                "rsrp_min": round(min(rsrp_vals), 1),
                "ta_range": ta_range,
                "ta_stable": ta_range < 10,
            },
            inferred_consequence=(
                f"Signal cliff detected: RSRP drop {rsrp_drop:.0f}dB with stable TA. "
                "Underground MRT transition likely. "
                "Subscribers transitioning from outdoor to underground — "
                "expect further SINR degradation without intervention."
            ),
            recommended_autonomous_action="SMALL_CELL_STEERING",
            severity=AlertSeverity.RED,
            metadata={"rsrp_recovery_expected": "micro-cell steering needed"},
        ))

    return events


# ── Internal helpers ──────────────────────────────────────────────────────────
def _rising_pct(values: list) -> float:
    if len(values) < 2:
        return 0.0
    return sum(1 for i in range(1, len(values)) if values[i] > values[i - 1]) / (len(values) - 1)


def _avg_trend(values: list) -> float:
    """Positive = rising, negative = falling."""
    if len(values) < 2:
        return 0.0
    mid = len(values) // 2
    first = values[:mid] or values
    second = values[mid:] or values
    return statistics.mean(second) - statistics.mean(first)


def _rsrp_to_qoe(rsrp: float, sinr: float) -> float:
    """Estimate QoE (0-100) from RSRP and SINR."""
    rsrp_factor = max(0, (rsrp + 120) / 30)   # -120 → 0, -90 → 1
    sinr_factor = max(0, sinr / 20)            # 0 → 0, 20 → 1
    return max(0, min(100, (rsrp_factor * 50) + (sinr_factor * 50)))
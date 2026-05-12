"""Pydantic data models for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Enums ───────────────────────────────────────────────────────────────────
class QoSClass(str, Enum):
    VIP_PREMIUM = "VIP_Premium"
    PREMIUM = "Premium"
    STANDARD = "Standard"
    BEST_EFFORT = "Best_Effort"


class SliceType(str, Enum):
    VIP_SLICE = "VIP_SLICE"
    PREMIUM_SLICE = "PREMIUM_SLICE"
    STANDARD_SLICE = "STANDARD_SLICE"
    BE_SLICE = "BE_SLICE"


class EventType(str, Enum):
    RRC_MEASUREMENT_REPORT = "RRC_MEASUREMENT_REPORT"
    HANDOVER_REQUEST = "HANDOVER_REQUEST"
    HANDOVER_COMPLETE = "HANDOVER_COMPLETE"
    PRB_THRESHOLD = "PRB_THRESHOLD"
    CONGESTION_DETECTED = "CONGESTION_DETECTED"
    SIGNAL_CLIFF = "SIGNAL_CLIFF"
    MULTIPATH_DETECTED = "MULTIPATH_DETECTED"


class AlertSeverity(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"
    PURPLE = "PURPLE"


# ── Telemetry Models ─────────────────────────────────────────────────────────
class UELocation(BaseModel):
    lat: float
    lon: float


class UEMetrics(BaseModel):
    rsrp: float = Field(description="Reference Signal Received Power (dBm)")
    sinr: float = Field(description="Signal to Interference plus Noise Ratio (dB)")
    ta: int = Field(description="Timing Advance (samples, ~78m each)")
    aoa: float = Field(description="Angle of Arrival (degrees)")
    throughput_mbps: float = Field(description="Throughput in Mbps")
    handover_success: bool = True
    packet_retransmission_rate: float = Field(default=0.0, le=1.0)
    prb_utilization: float = Field(ge=0, le=100, description="Physical Resource Block utilization %")
    cqi: int = Field(ge=0, le=15, description="Channel Quality Indicator")


class UETelemetry(BaseModel):
    timestamp: datetime
    ue_id: str = Field(description="Hashed UE identifier")
    qos_class: QoSClass
    slice_type: SliceType
    cell_id: str
    sector_id: str
    event: EventType
    metrics: UEMetrics
    location: UELocation
    distance_to_mrt_m: float = Field(default=0.0, description="Distance from MRT station")


class Subscriber(BaseModel):
    ue_id: str
    qos_class: QoSClass
    slice_type: SliceType
    is_vip: bool = False
    name: Optional[str] = None
    current_telemetry: Optional[UETelemetry] = None
    rsrp_history: list[float] = Field(default_factory=list, max_length=60)
    sinr_history: list[float] = Field(default_factory=list, max_length=60)
    ta_history: list[int] = Field(default_factory=list, max_length=60)
    handover_count: int = 0
    frustration_index: float = Field(default=0.0, ge=0, le=100)
    qoe_degradation_predicted_min: float = Field(default=999.0, description="Minutes until predicted QoE degradation")
    qoe_trend: float = Field(default=0.0, description="QoE trend direction (positive=improving)")


class CellState(BaseModel):
    cell_id: str
    name: str
    lat: float
    lon: float
    cell_type: str
    active_ues: int = 0
    prb_utilization: float = 0.0
    avg_rsrp: float = -100.0
    avg_sinr: float = 10.0
    handover_requests: int = 0
    handover_success_rate: float = 100.0
    throughput_mbps_avg: float = 0.0


# ── KPI Models ──────────────────────────────────────────────────────────────
class KPIState(BaseModel):
    timestamp: datetime
    subscriber_satisfaction_score: float = Field(ge=0, le=100, default=85.0)
    vip_qoe_score: float = Field(ge=0, le=100, default=90.0)
    congestion_risk: float = Field(ge=0, le=100, default=20.0)
    ai_confidence: float = Field(ge=0, le=100, default=75.0)
    sla_health: float = Field(ge=0, le=100, default=95.0)
    revenue_protection_usd: float = 0.0
    predicted_mobility_pressure: float = Field(ge=0, le=100, default=30.0)
    congestion_prevented: float = 0.0
    estimated_sla_savings_usd: float = 0.0
    ai_mitigation_success_rate: float = 0.0
    vip_retention_risk_reduction: float = 0.0


# ── RAN Alert Models ─────────────────────────────────────────────────────────
class RANAlert(BaseModel):
    timestamp: datetime
    alert_type: str
    severity: AlertSeverity
    cell_id: Optional[str] = None
    reason: str
    supporting_telemetry: dict
    confidence_score: float = Field(ge=0.0, le=100.0)
    recommended_action: Optional[str] = None


# ── Mobility Models ─────────────────────────────────────────────────────────
class MRTExit(BaseModel):
    exit_id: str
    name: str
    lat: float
    lon: float
    congestion_level: str = "GREEN"
    current_load: int = 0
    capacity: int = 300


class MobilityState(BaseModel):
    timestamp: datetime
    crowd_density_arena: int = 0
    crowd_density_mrt: int = 0
    total_subscribers: int = 0
    mrt_exits: list[MRTExit] = Field(default_factory=list)
    overall_congestion: str = "GREEN"
    youbike_available: int = 12
    youbike_empty_docks: int = 8
    walking_propensity: float = 1.0  # 0.0-1.0
    slip_risk: str = "LOW"
    crowd_pressure_propagation: float = 0.0
    mass_egress_detected: bool = False
    egress_velocity_kmh: float = 0.0


# ── Weather Models ───────────────────────────────────────────────────────────
class WeatherState(BaseModel):
    timestamp: datetime
    rainfall_mm_hr: float = 0.0
    temperature_c: float = 25.0
    humidity_pct: float = 60.0
    wind_speed_ms: float = 0.0
    condition: str = "clear"
    source: str = "CWA"


# ── Autonomous Action Models ─────────────────────────────────────────────────
class AutonomousAction(BaseModel):
    action_id: str
    action_type: str  # VIP_PRIORITY_ROUTING, LOAD_BALANCING, MICRO_CELL_HO, etc.
    timestamp: datetime
    confidence_score: float = Field(ge=0.0, le=100.0)
    reason: str
    expected_kpi_improvement_pct: float = 0.0
    expected_congestion_reduction_pct: float = 0.0
    status: str = "proposed"
    policy_approved: bool = False
    policy_reject_reason: Optional[str] = None
    executed: bool = False


# ── Policy Decision ──────────────────────────────────────────────────────────
class PolicyDecision(BaseModel):
    action: AutonomousAction
    approved: bool
    reasoning: str
    conditions: list[str] = Field(default_factory=list)


# ── AI Reasoning Entry ───────────────────────────────────────────────────────
class AgentReasoningEntry(BaseModel):
    timestamp: datetime
    agent_name: str
    agent_type: str  # RAN, MOBILITY, CONTEXT, POLICY, INTENT
    reasoning: str
    confidence: float = Field(ge=0.0, le=100.0)
    triggered_action: Optional[str] = None
    color: str = "cyan"  # cyan, green, orange, red, purple
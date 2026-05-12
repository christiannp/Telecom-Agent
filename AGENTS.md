# Multi-Agent System

The platform uses **Google ADK** to orchestrate 5 specialist agents plus a root Intent Orchestration Agent.

---

## 1. Intent Orchestration Agent (`root_agent`)

**Role**: Primary AI interface coordinating all specialist agents

**Capabilities**:
- Interprets user queries ("Analyze concert exit", "Show VIP congestion risk")
- Coordinates RAN, Mobility, Context, and Policy agents
- Provides unified operational intelligence
- Explains AI reasoning with confidence scores

**Tools**: All 7 ADK tools (RAN state, mobility state, KPI dashboard, subscriber info, VIP info, action validation, action execution)

---

## 2. RAN Intelligence Agent (`ran_intelligence_agent`)

**Role**: Radio Access Network analysis and optimization

**Capabilities**:
- **Timing Advance Distance**: `Distance ≈ TA × 78 meters`
- **Mass Egress Detection**: 70%+ subscribers with increasing TA
- **Signal Cliff Detection**: RSRP drop > 15dB with stable TA → underground transition
- **Multi-path Interference**: High AoA variance → arena architecture impact
- **Congestion Detection**: PRB utilization > 80%
- **Handover Failure Prediction**: Based on SINR + RSRP degradation
- **Anomaly Burst Detection**: CQI drops to 2-3 across 20% of UEs for sustained periods
- **Multi-Cell Handover Storm Detection**: 30%+ handover failure rate during underground transition

**Key Metrics**:
- RSRP (Reference Signal Received Power): -44 to -140 dBm
- SINR (Signal to Interference plus Noise Ratio): 0-30 dB
- PRB (Physical Resource Block): 0-100% utilization
- CQI (Channel Quality Indicator): 0-15

---

## 3. Mobility Intelligence Agent (`mobility_intelligence_agent`)

**Role**: Urban mobility and crowd dynamics analysis

**Capabilities**:
- MRT congestion monitoring (GREEN/YELLOW/RED per exit)
- YouBike station 500101077 availability tracking
- Mass egress velocity estimation (km/h)
- Walking propensity calculation (weather-adjusted)
- Slip risk assessment (rainfall-based)
- Crowd pressure propagation modeling
- YouBike Starvation Detection: all docks empty → crowd backs up → frustration rises

**Data Sources**:
- Nanjing Fuxing MRT Station (3 exits, 800 capacity each)
- YouBike Arena Station (60 docks, real-time availability)
- Taipei Arena → MRT distance: 450m

---

## 4. Context Intelligence Agent (`context_intelligence_agent`)

**Role**: Environmental awareness and impact analysis

**Capabilities**:
- Taiwan CWA weather integration (Songshan District)
- Rainfall impact on mobility (7.2mm/hr → 40% MRT preference increase)
- Slip risk calculation (LOW/MODERATE/HIGH/SEVERE)
- Walking propensity estimation (0.0-1.0 scale)
- Temperature/humidity/wind monitoring
- Weather Transition Detection: rainfall spike from 0 → 12 mm/hr at tick ~50

**Weather Logic**:
- Rainfall > 5mm/hr: High slip risk, reduced walking propensity
- Rainfall > 10mm/hr: Severe risk, majority avoid walking
- Weather affects subscriber behavior → network load patterns

---

## 5. Policy Validation Agent (`policy_validation_agent`)

**Role**: Autonomous action governance and SLA enforcement

**Capabilities**:
- Validates actions against confidence threshold (≥85%)
- Enforces VIP SLA policy (VIP QoE must remain >80)
- Prevents unstable optimization loops
- Validates congestion reduction (≥5% improvement required)
- Loop Detection: blocks load-balancing actions that would overload neighboring cells
- Logs all decisions to `logs/policy_decisions.log`

**Policy Rules**:
- VIP Priority Routing: requires ≥10% expected KPI improvement
- Load Balancing: must not cause neighboring cell overload
- All actions: must improve VIP SLA without worsening congestion elsewhere

---

## ADK Tools (7 tools)

| Tool | Purpose |
|------|---------|
| `get_ran_state` | Returns current RSRP, SINR, TA, PRB, CQI per UE |
| `get_mobility_state` | Returns MRT congestion status, YouBike availability |
| `get_kpi_dashboard` | Returns executive KPIs (satisfaction, VIP QoE, congestion risk) |
| `get_subscriber_info` | Returns subscriber-level QoE and degradation |
| `get_vip_info` | Returns VIP subscriber tracking and SLA status |
| `validate_action` | Policy-checks an action before execution |
| `trigger_autonomous_action` | Executes a validated autonomous action |

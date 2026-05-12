"""
Multi-agent Google ADK setup for CovMo Telecom Intelligence Platform.

Agents:
- Intent Orchestration Agent (root): coordinates all sub-agents
- RAN Intelligence Agent: radio metric analysis
- Mobility Intelligence Agent: crowd movement analysis
- Context Intelligence Agent: weather & environmental awareness
- Policy Validation Agent: autonomous action governance

AGENTIC AI SKILLS IMPLEMENTED (per Master Prompt.md):
  ┌──────────────────────────┬──────────────────────────────────────────────────┐
  │ SKILL                    │ IMPLEMENTATION                                 │
  ├──────────────────────────┼──────────────────────────────────────────────────┤
  │ TOOL USE                 │ Scoped domain + skill tools wired per-agent    │
  │ SUB-AGENT DELEGATION     │ root → 4 specialist agents                     │
  │ MEMORY                   │ store/get_agent_memory, cross-turn continuity  │
  │ EVENT CORRELATION        │ correlate_events_tool — 6 scenario detectors    │
  │ TIME-SERIES ANALYTICS    │ get_time_series_stats + get_anomaly_report      │
  │ INCIDENT REPLAY          │ save_snapshot + control_replay + get_replay_*   │
  │ MONITORING LOOP          │ start/run/stop_continuous_monitoring            │
  │ REASONING LOG            │ log_agent_reasoning — explainability            │
  │ AUTONOMOUS ACTIONS       │ validate_autonomous_action + trigger_autonomous│
  │ PLANNING                 │ Structured reasoning summaries in instructions  │
  └──────────────────────────┴──────────────────────────────────────────────────┘
"""
from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models import LiteLlm

from config import LLM_MODEL

# ── Tool Imports ─────────────────────────────────────────────────────────────
# Base domain tools (existing)
from tools import (
    get_ran_state,
    get_mobility_state,
    get_weather_state,
    predict_mrt_overload,
    get_kpi_dashboard,
    get_subscriber_info,
    get_all_vip_info,
    validate_autonomous_action,
    trigger_autonomous_action,
)

# NEW — Agentic AI Skill tools
from tools import (
    log_agent_reasoning,
    get_memory,
    get_reasoning_log,
    clear_memory,
    correlate_events_tool,
    get_time_series_stats,
    get_anomaly_report,
    save_snapshot,
    get_replay_range,
    control_replay,
    get_replay_status,
    start_continuous_monitoring,
    run_monitoring_check,
    stop_continuous_monitoring,
    get_monitoring_status,
)


# ══════════════════════════════════════════════════════════════════════════════
# SCOPED TOOL SETS
# ══════════════════════════════════════════════════════════════════════════════

# RAN owns radio telemetry, subscriber radio quality, and radio-centric analytics.
RAN_TOOLS = [
    get_ran_state,
    get_subscriber_info,
    get_all_vip_info,
    get_kpi_dashboard,
    correlate_events_tool,
    get_time_series_stats,
    get_anomaly_report,
    log_agent_reasoning,
    get_memory,
    start_continuous_monitoring,
    run_monitoring_check,
]

# Mobility owns crowd movement, transport pressure, and mobility forecasting.
MOBILITY_TOOLS = [
    get_mobility_state,
    predict_mrt_overload,
    get_kpi_dashboard,
    get_time_series_stats,
    get_anomaly_report,
    log_agent_reasoning,
    get_memory,
    start_continuous_monitoring,
    run_monitoring_check,
]

# Context owns weather/environment awareness and weather-to-network correlation.
CONTEXT_TOOLS = [
    get_weather_state,
    get_mobility_state,
    get_kpi_dashboard,
    correlate_events_tool,
    get_time_series_stats,
    log_agent_reasoning,
    get_memory,
    start_continuous_monitoring,
    run_monitoring_check,
]

# Policy owns governance, autonomous action validation/execution, and loop safety.
POLICY_TOOLS = [
    validate_autonomous_action,
    trigger_autonomous_action,
    get_kpi_dashboard,
    get_all_vip_info,
    get_anomaly_report,
    log_agent_reasoning,
    get_memory,
    start_continuous_monitoring,
    run_monitoring_check,
    get_monitoring_status,
]

# Root orchestrator stays intentionally thin. Domain data and actions belong to
# specialist agents; root keeps coordination, memory, replay, and status tools.
ORCHESTRATOR_TOOLS = [
    log_agent_reasoning,
    get_memory,
    get_reasoning_log,
    clear_memory,
    save_snapshot,
    get_replay_range,
    control_replay,
    get_replay_status,
    stop_continuous_monitoring,
    get_monitoring_status,
]


# ══════════════════════════════════════════════════════════════════════════════
# RAN INTELLIGENCE AGENT
# Skill: TOOL USE ✅ | EVENT CORRELATION ✅ | TIME-SERIES ✅ | MEMORY ✅
#        MONITORING LOOP ✅ | PLANNING ✅ | AUTONOMOUS ✅ (via root)
# ══════════════════════════════════════════════════════════════════════════════
RAN_INSTRUCTION = """You are the CovMo RAN Intelligence Agent.

You specialize in:
- Analyzing radio metrics: RSRP, SINR, Timing Advance, AOA, CQI, PRB utilization
- Detecting congestion patterns and signal cliffs
- Predicting handover failures and multi-path interference
- Evaluating radio coverage quality
- Recommending autonomous radio optimization actions

Key RAN concepts:
- RSRP (Reference Signal Received Power): -44 to -140 dBm. Good > -90 dBm, Poor < -105 dBm
- SINR (Signal to Interference plus Noise Ratio): 0-30 dB. Good > 15 dB, Poor < 8 dB
- Timing Advance (TA): indicates distance from cell. Distance ≈ TA × 78 meters
- PRB (Physical Resource Block): 0-100%. Congestion concern > 80%
- Signal Cliff: RSRP drop > 15 dB while TA stays stable → underground transition

TOOL SET (AGENTIC SKILLS YOU CAN EXECUTE):
1. get_ran_state()         — live cell metrics and RAN alerts
2. get_subscriber_info()    — single subscriber radio/QoE drill-down
3. get_all_vip_info()       — VIP subscriber radio quality
4. get_kpi_dashboard()       — executive KPIs
5. correlate_events_tool()  — EVENT CORRELATION: correlate TA/RSRP/AoA/weather signals
                              into unified scenario inferences (6 scenarios detected)
6. get_time_series_stats()  — TIME-SERIES: rolling mean/std, trend, anomaly, forecast
                              for any metric: rsrp, sinr, ta, prb_utilization, throughput_mbps
7. get_anomaly_report()     — anomaly detection across all metrics with sigma severity
8. log_agent_reasoning()    — REASONING LOG: store your reasoning summary with confidence
9. get_memory()             — MEMORY: recall previous analysis steps for continuity
10. start_continuous_monitoring() — MONITOR LOOP: activate autonomous watch mode
11. run_monitoring_check()  — escalate or de-escalate based on persistent alerts

WORKFLOW (reasoning summary, execute in order):
1. Call get_ran_state() to get live metrics and alerts
2. Call get_time_series_stats("rsrp") and get_time_series_stats("sinr") for trend analysis
3. Call get_anomaly_report() to detect statistical outliers
4. Call correlate_events_tool() to infer operational scenarios
5. Call get_memory(agent_name="ran_intelligence_agent") for recent RAN continuity
6. If conditions warrant, call start_continuous_monitoring(agent_name="ran_intelligence_agent")
   then run_monitoring_check(agent_name="ran_intelligence_agent")
7. Call log_agent_reasoning() with your complete analysis, confidence score, and action
8. Respond in this structure:
   - Root-cause analysis
   - Confidence score (0-100%)
   - Supporting telemetry evidence
   - Specific recommended autonomous action (action type)
   - Estimated KPI improvement

Use telecom-native terminology. Be precise and operationally focused."""

ran_agent = LlmAgent(
    model=LiteLlm(model=LLM_MODEL),
    name="ran_intelligence_agent",
    description="CovMo RAN Intelligence — analyzes radio metrics, detects congestion and signal cliffs.",
    instruction=RAN_INSTRUCTION,
    tools=RAN_TOOLS,
)


# ══════════════════════════════════════════════════════════════════════════════
# MOBILITY INTELLIGENCE AGENT
# Skill: TOOL USE ✅ | TIME-SERIES ✅ | MEMORY ✅ | MONITORING LOOP ✅
#        PLANNING ✅ | AUTONOMOUS ✅
# ══════════════════════════════════════════════════════════════════════════════
MOBILITY_INSTRUCTION = """You are the CovMo Mobility Intelligence Agent.

You specialize in:
- Urban mobility patterns and crowd dynamics
- MRT (Mass Rapid Transit) congestion analysis
- YouBike availability optimization
- Mass egress detection from large venues
- Walking propensity estimation based on weather
- Slip risk assessment
- Intermodal transportation coordination

Key concepts:
- Taipei Arena → Nanjing Fuxing MRT mass egress scenario
- Exit congestion levels: GREEN (<50%), YELLOW (50-80%), RED (>80%)
- YouBike station 500101077 near Taipei Arena
- Rainfall > 5 mm/hr significantly increases MRT preference
- Slip risk escalates with rainfall intensity

TOOL SET (AGENTIC SKILLS YOU CAN EXECUTE):
1. get_mobility_state()     — MRT congestion, YouBike availability, mass egress status
2. predict_mrt_overload()   — forecast MRT overload risk for N minutes ahead
3. get_kpi_dashboard()      — executive KPIs
4. get_time_series_stats()  — TIME-SERIES: trend analysis on crowd/mobility metrics
5. get_anomaly_report()     — anomaly detection across mobility metrics
6. log_agent_reasoning()    — REASONING LOG: store your reasoning summary
7. get_memory()             — MEMORY: recall previous mobility analysis for continuity
8. start_continuous_monitoring() — MONITOR LOOP: activate autonomous crowd watch mode
9. run_monitoring_check()   — escalate if congestion persists across cycles

WORKFLOW:
1. Call get_mobility_state() for current MRT/YouBike/exit status
2. Call predict_mrt_overload(minutes_ahead=10) for 10-min risk forecast
3. Call get_time_series_stats("ta") to track crowd approach velocity
4. Call get_memory(agent_name="mobility_intelligence_agent") to recall previous crowd analysis
5. If congestion rising, call start_continuous_monitoring(agent_name="mobility_intelligence_agent")
   then run_monitoring_check(agent_name="mobility_intelligence_agent")
6. Call log_agent_reasoning() with full analysis and recommended actions
7. Respond in this structure:
   - Current crowd density and flow patterns
   - MRT congestion forecast (5-10 min horizon)
   - Weather impact on mobility choices
   - Transportation pressure assessment
   - Recommended actions to prevent overload

Use urban mobility and transportation terminology."""

mobility_agent = LlmAgent(
    model=LiteLlm(model=LLM_MODEL),
    name="mobility_intelligence_agent",
    description="CovMo Mobility Intelligence — analyzes crowd movement and urban transportation.",
    instruction=MOBILITY_INSTRUCTION,
    tools=MOBILITY_TOOLS,
)


# ══════════════════════════════════════════════════════════════════════════════
# CONTEXT INTELLIGENCE AGENT
# Skill: TOOL USE ✅ | EVENT CORRELATION ✅ | MEMORY ✅ | MONITORING LOOP ✅
#        PLANNING ✅ | AUTONOMOUS ✅
# ══════════════════════════════════════════════════════════════════════════════
CONTEXT_INSTRUCTION = """You are the CovMo Context Intelligence Agent.

You specialize in:
- Weather impact on telecom operations
- Environmental factor analysis
- Slip risk prediction for outdoor subscribers
- Walking propensity estimation
- Rainfall effects on radio propagation (attenuation)
- Temperature impact on network equipment

Key concepts:
- Rainfall > 5 mm/hr: reduces walking propensity, increases MRT/taxi preference
- Rainfall > 10 mm/hr: severe slip risk, majority avoid walking
- Weather affects subscriber behavior, which affects network load
- Taiwan CWA (Central Weather Administration) data
- Weather → MRT pressure → RAN congestion cascade

TOOL SET (AGENTIC SKILLS YOU CAN EXECUTE):
1. get_weather_state()      — current rainfall, temperature, humidity, slip risk, walking propensity
2. get_mobility_state()     — mobility impact from weather (walking propensity, MRT preference)
3. get_kpi_dashboard()      — executive KPIs
4. get_time_series_stats()  — TIME-SERIES: track network-impact metrics affected by weather
5. correlate_events_tool()   — EVENT CORRELATION: link rainfall → walking propensity → MRT load → RAN
6. log_agent_reasoning()    — REASONING LOG: explain weather → network behavior chain
7. get_memory()             — MEMORY: recall previous weather impact analysis
8. start_continuous_monitoring() — MONITOR LOOP: watch for dangerous weather escalation
9. run_monitoring_check()   — escalate if rainfall or slip risk intensifies

WORKFLOW:
1. Call get_weather_state() to get current conditions and slip risk
2. Call get_mobility_state() to see weather-adjusted mobility impact
3. Call get_time_series_stats("rsrp") to correlate weather with signal degradation
4. Call correlate_events_tool() to trace the full causal chain:
      Rainfall → Walking propensity → MRT pressure → RAN congestion → VIP QoE
5. Call get_memory(agent_name="context_intelligence_agent") to recall previous weather context
6. If rainfall > 5 mm/hr or slip risk HIGH, call
   start_continuous_monitoring(agent_name="context_intelligence_agent")
   then run_monitoring_check(agent_name="context_intelligence_agent")
7. Call log_agent_reasoning() explaining the full weather impact chain
8. Respond in this structure:
   - Current weather conditions and trend
   - Impact on subscriber behavior and network load
   - Safety risk assessment
   - Correlation with network quality degradation
   - Recommendations for weather-adaptive operations

Use environmental science and telecom operations terminology."""

context_agent = LlmAgent(
    model=LiteLlm(model=LLM_MODEL),
    name="context_intelligence_agent",
    description="CovMo Context Intelligence — weather and environmental awareness.",
    instruction=CONTEXT_INSTRUCTION,
    tools=CONTEXT_TOOLS,
)


# ══════════════════════════════════════════════════════════════════════════════
# POLICY VALIDATION AGENT
# Skill: TOOL USE ✅ | AUTONOMOUS ACTION ✅ | MEMORY ✅ | MONITORING LOOP ✅
#        PLANNING ✅ (policy reasoning) | REASONING LOG ✅
# ══════════════════════════════════════════════════════════════════════════════
POLICY_INSTRUCTION = """You are the CovMo Policy Validation Agent.

You specialize in:
- Validating autonomous AI actions before execution
- Enforcing telecom operational governance
- VIP SLA policy enforcement
- Preventing unstable optimization loops
- Risk assessment for autonomous actions
- Regulatory compliance for telecom operations

Policy rules (do NOT deviate):
- Confidence threshold: ≥ 85% for autonomous action approval
- VIP SLA: VIP subscribers must maintain QoE > 80
- Congestion reduction: load balancing actions must yield ≥ 5% improvement
- VIP Priority Routing: requires ≥ 10% expected KPI improvement
- Neighboring cell overload: actions must not cause secondary congestion
- Only approved action types allowed:
    VIP_PRIORITY_ROUTING, TEMPORARY_LOAD_BALANCING, MICRO_CELL_HANDOVER,
    DYNAMIC_SLICE_ALLOCATION, SLEEP_MODE_COORDINATION, ANTENNA_TILT_OPTIMIZATION,
    NEIGHBOR_CELL_EXPANSION, SMALL_CELL_STEERING, PRIORITY_SCHEDULING

TOOL SET (AGENTIC SKILLS YOU CAN EXECUTE):
1. validate_autonomous_action()  — validate action against all policy rules
2. trigger_autonomous_action()   — execute a policy-approved action (requires approval first)
3. get_kpi_dashboard()           — current KPI state for risk assessment
4. get_all_vip_info()            — VIP SLA context before approving subscriber-impacting actions
5. get_anomaly_report()          — TIME-SERIES: check for anomalies before approving actions
6. log_agent_reasoning()          — REASONING LOG: document policy decision with full justification
7. get_memory()                   — MEMORY: recall previous policy decisions for loop prevention
8. start_continuous_monitoring()  — MONITOR LOOP: watch for optimization loop instability
9. run_monitoring_check()         — escalate if the same action is being validated repeatedly
10. get_monitoring_status()       — inspect current governance watch state

WORKFLOW (AGENTIC AUTONOMOUS DECISION LOOP):
1. When validate_autonomous_action() is called with an action_json:
   a. Call get_kpi_dashboard() to assess current system state
   b. Call get_all_vip_info() for VIP SLA exposure
   c. Call get_anomaly_report() to check for active anomalies
   d. Apply all 5 policy rule checks (confidence, action type, KPI, VIP SLA, congestion)
   e. Check get_memory(agent_name="policy_validation_agent") and
      get_monitoring_status(agent_name="policy_validation_agent") for recent same/similar actions
   f. If action is same as recent → flag unstable optimization loop risk
   g. Call log_agent_reasoning() with full policy decision and reasoning
   h. Return approval or rejection with detailed conditions

2. When a VIP SLA violation is detected:
   a. Call start_continuous_monitoring(agent_name="policy_validation_agent") for policy watch mode
   b. Prioritize VIP_PRIORITY_ROUTING and SMALL_CELL_STEERING actions
   c. Call log_agent_reasoning() with VIP SLA impact reasoning

3. Respond in this structure:
   - Clear approval or rejection
   - Detailed policy reasoning (rule-by-rule)
   - Conditions met or violated
   - Risk assessment
   - Alternative recommendations if rejected

Use governance and telecom policy terminology."""

policy_agent = LlmAgent(
    model=LiteLlm(model=LLM_MODEL),
    name="policy_validation_agent",
    description="CovMo Policy Validation — validates autonomous actions against operational policies.",
    instruction=POLICY_INSTRUCTION,
    tools=POLICY_TOOLS,
)


# ══════════════════════════════════════════════════════════════════════════════
# INTENT ORCHESTRATION AGENT (ROOT)
# Skill: SUB-AGENT DELEGATION ✅ | MEMORY ✅ | INCIDENT REPLAY ✅
#        MONITORING STATUS ✅ | PLANNING ✅ | REASONING LOG ✅
# ══════════════════════════════════════════════════════════════════════════════
INTENT_INSTRUCTION = """You are the CovMo Intent Orchestration Agent — the primary AI interface for the CovMo Telecom Intelligence Platform.

You coordinate all sub-agents to provide unified telecom operational intelligence.

Your personality:
- Professional, operationally precise
- Uses telecom-native terminology
- Explains AI reasoning transparently
- Always provides confidence scores
- Recommends specific autonomous actions

You coordinate these specialist agents:
1. **RAN Intelligence**: Radio metrics, congestion, signal quality, multi-path, handover failures
2. **Mobility Intelligence**: Crowd movement, MRT, YouBike, mass egress, exit flow
3. **Context Intelligence**: Weather, environment, slip risk, weather → network correlation
4. **Policy Validation**: Action governance, SLA enforcement, loop prevention

Scenario: Taipei Arena "Power Station" Concert Egress
- May 15, 2026, 22:00 mass exit
- ~1500 subscribers moving from Taipei Arena to Nanjing Fuxing MRT
- Light rain (7.2 mm/hr) increasing MRT pressure
- AI continuously monitors and recommends autonomous optimizations

ROOT TOOL SET — ORCHESTRATION ONLY:
- get_reasoning_log()        — read specialist conclusions already logged
- get_memory(agent_name)     — recall prior outputs from any specialist agent
- log_agent_reasoning()      — record orchestration summary and final confidence
- clear_memory(agent_name)   — reset memory only when explicitly requested
- save_snapshot()            — save point-in-time orchestration output for replay
- get_replay_range()         — retrieve replay snapshots by tick range
- control_replay()           — replay controls: play, pause, stop, speed, seek
- get_replay_status()        — current replay playback state
- stop_continuous_monitoring(agent_name) — stop a specialist monitoring loop when requested
- get_monitoring_status()    — summarize active specialist monitoring loops

Tools intentionally NOT owned by root:
- RAN data, subscriber data, VIP radio quality, KPI/time-series/anomaly reads → delegate to RAN Intelligence
- MRT, YouBike, crowd-flow, transport forecast reads → delegate to Mobility Intelligence
- Weather, slip risk, environmental-cascade analysis → delegate to Context Intelligence
- Action validation and execution → delegate to Policy Validation

MANDATORY ORCHESTRATION WORKFLOW (execute every user query):
1. Classify the user intent and delegate to the relevant specialist agent(s).
2. For cross-domain incidents, delegate in this order: Context → Mobility → RAN → Policy.
3. Call get_reasoning_log() and get_memory(agent_name="...") for relevant specialists.
4. If an autonomous action is proposed, send it to Policy Validation before presenting it as executable.
5. Call log_agent_reasoning() with a concise orchestration summary, confidence score, and policy status.
6. Call save_snapshot() after material incident analysis or replay-worthy decisions.

INCIDENT REPLAY: When user asks "replay from 22:05" or similar:
1. Call get_replay_range(start_tick, end_tick) to fetch snapshots
2. Call control_replay("play", speed=X) to start replay
3. Present replay in time-sorted reasoning log format

Always respond in this structure:
1. **Executive Summary**: One-sentence operational status
2. **Delegated Analysis**: Specialist agents consulted and their findings
3. **Event Correlation**: Cross-domain scenarios reported by specialists
4. **Time-Series Insights**: Trends/anomalies reported by the owning specialist
5. **AI Reasoning**: Concise orchestration rationale from logged specialist summaries
6. **Recommendations**: Specific autonomous actions with confidence scores and policy status
7. **Supporting Evidence**: Key telemetry values cited from specialist outputs

This is an operational intelligence platform — NOT a chatbot. Be precise, technical, and actionable."""

root_agent = LlmAgent(
    model=LiteLlm(model=LLM_MODEL),
    name="root_agent",
    description=(
        "CovMo Intent Orchestration — coordinates all AI agents to provide "
        "real-time telecom operational intelligence for the Taipei Arena mass egress scenario."
    ),
    instruction=INTENT_INSTRUCTION,
    sub_agents=[
        ran_agent,
        mobility_agent,
        context_agent,
        policy_agent,
    ],
    tools=ORCHESTRATOR_TOOLS,
)

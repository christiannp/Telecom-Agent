# User Guide — Questions Users Can Ask

The ADK multi-agent system accepts natural-language queries and routes them to the appropriate specialist agent. Below are example questions organized by domain.

---

## General / Orchestrator

- **"What is happening right now in the network?"**
  → Orchestrator coordinates all agents and returns a unified situational summary with confidence scores.

- **"Give me a complete status report of the Taipei Arena scenario."**
  → Orchestrator aggregates RAN, mobility, weather, and policy state into a single briefing.

- **"Should I be concerned about anything in the next 5 minutes?"**
  → Orchestrator invokes all agents to predict near-term risks and prioritizes by SLA impact.

- **"Summarize the AI reasoning behind recent autonomous actions."**
  → Orchestrator retrieves and explains the chain-of-thought from each agent that contributed to recent actions.

---

## RAN Intelligence

- **"Show me all active signal cliffs and handover failure rates."**
  → RAN agent returns current RSRP cliff events, SINR degradation zones, and per-cell handover success rates.

- **"Which cells are experiencing congestion right now?"**
  → RAN agent lists cells with PRB > 80%, their subscriber counts, and recommended actions.

- **"Is there a mass egress pattern forming? How many UEs are affected?"**
  → RAN agent detects increasing TA across 70%+ of UEs and estimates crowd velocity and direction.

- **"What is causing the CQI anomaly in the underground MRT zone?"**
  → RAN agent runs anomaly detection on the time-series CQI data and identifies the affected UE group.

- **"Compare VIP subscriber signal quality vs standard subscribers."**
  → RAN agent retrieves VIP vs standard RSRP/SINR statistics and calculates the gap.

- **"Predict handover failures in the next 60 seconds."**
  → RAN agent uses SINR + RSRP trend analysis to forecast cells at risk of >20% handover failure.

- **"Generate a full anomaly report for the last 10 minutes."**
  → RAN agent calls `get_anomaly_report()` and returns a formatted diagnostic summary.

---

## Mobility Intelligence

- **"What is the current MRT congestion status at each exit?"**
  → Mobility agent returns GREEN/YELLOW/RED status per exit with crowd counts and capacity utilization.

- **"Are there any YouBike docks available near the arena?"**
  → Mobility agent queries YouBike availability and reports station 500101077 status (60 docks, current availability).

- **"How bad is the crowd backup at the MRT entrance?"**
  → Mobility agent calculates crowd pressure, propagation delay, and frustration index.

- **"What will the mobility pressure be in 10 minutes given the current egress rate?"**
  → Mobility agent projects crowd arrival rate at MRT based on TA velocity and walking propensity.

- **"Should I reroute some subscribers to a different MRT exit?"**
  → Mobility agent evaluates exit load distribution and recommends balancing if one exit exceeds 85% capacity.

- **"What is the slip risk for pedestrians right now?"**
  → Mobility agent retrieves weather-adjusted slip risk (LOW/MODERATE/HIGH/SEVERE) based on rainfall intensity.

---

## Context Intelligence

- **"How is the current weather affecting subscriber behavior?"**
  → Context agent explains rainfall impact on walking propensity and MRT preference shift.

- **"What is the current weather in Songshan District?"**
  → Context agent returns temperature, humidity, wind speed, and rainfall (mm/hr) from Taiwan CWA.

- **"If it rains harder, how will that impact the network?"**
  → Context agent models the effect of increased rainfall (e.g., 12 → 20 mm/hr) on mobility and RAN load.

- **"Calculate the walking propensity for the current weather conditions."**
  → Context agent returns a 0.0–1.0 walking propensity score and explains contributing factors.

- **"What is the combined weather + crowd risk score?"**
  → Context agent fuses rainfall, slip risk, crowd density, and MRT congestion into a unified risk score.

---

## Policy Validation

- **"Should I enable VIP Priority Routing right now?"**
  → Policy agent validates the action against current KPIs, requires ≥85% confidence and ≥10% expected improvement.

- **"Show me the last 5 autonomous actions and their policy decisions."**
  → Policy agent retrieves recent decisions from `logs/policy_decisions.log` with reasoning and approval status.

- **"Would load balancing to the neighboring cell cause a secondary congestion?"**
  → Policy agent runs loop detection: simulates the load-balance action and blocks it if neighboring cell PRB would exceed 85%.

- **"Is the VIP SLA at risk? What is the current VIP QoE score?"**
  → Policy agent returns VIP QoE (0–100%) and SLA health, flagging if it is approaching the <80 breach threshold.

- **"What is the confidence score for the current autonomous action?"**
  → Policy agent reports confidence level and lists the conditions that must be met for approval.

- **"Revert the last autonomous action."**
  → Policy agent validates the rollback request and triggers `trigger_autonomous_action()` with rollback semantics.

---

## Subscriber & VIP Analytics

- **"Show me the top 10 VIP subscribers by QoE degradation."**
  → Returns VIP subscribers sorted by largest QoE drop, with current RSRP, SINR, and predicted SLA breach time.

- **"Which subscribers are experiencing the worst signal quality?"**
  → Returns subscribers with lowest RSRP/SINR, grouped by location (arena, transit, MRT underground).

- **"What is the overall subscriber satisfaction score?"**
  → Returns the executive KPI: Subscriber Satisfaction Score (0–100%) with trend over the last 50 ticks.

- **"Predict which VIP subscribers will breach SLA in the next 5 minutes."**
  → Uses RAN + mobility trend analysis to predict VIP QoE drop below 80 and estimates time-to-breach.

---

## KPI & Executive Dashboard

- **"What are the current executive KPIs?"**
  → Returns Subscriber Satisfaction, VIP QoE, Congestion Risk, AI Confidence, SLA Health, Revenue Protection (USD), and Mobility Pressure.

- **"How much revenue has been protected by autonomous actions today?"**
  → Policy agent calculates revenue protected by preventing VIP SLA breaches.

- **"Show me the KPI trend chart for the last 30 minutes."**
  → Returns Plotly chart data for all executive KPIs over the specified window.

- **"What is the AI confidence level for the current operational state?"**
  → Returns the AI Confidence KPI (0–100%) based on model agreement across all active agents.

---

## Correlated Events & Scenario Detection

- **"What correlated scenarios are active right now?"**
  → Returns output from `correlate_events()`: the 6 unified scenario detectors (signal cliff + underground transition, mass egress + MRT overload, weather shift + walking propensity, etc.).

- **"Are there any cross-domain anomalies that suggest a cascading failure?"**
  → Correlation pipeline detects when RAN degradation + mobility congestion + weather shift occur simultaneously and alerts.

- **"Show me the monitoring escalation level."**
  → Returns current escalation level (1–4) from `run_monitoring_check()`: INFO → WARN → ELEVATED → CRITICAL.

---

## Incident Replay

- **"Save a snapshot of the current state."**
  → Triggers `save_snapshot()` at the current tick for later replay.

- **"Replay the VIP degradation incident from tick 70 to 90."**
  → Loads the snapshot saved at tick ~80 (first RED alert / VIP SLA breach) and replays telemetry in scrubbed mode.

- **"What happened during the handover storm incident?"**
  → Replays the incident arc captured between phases 0.65–0.80, showing the RAN agent's reasoning and actions taken.

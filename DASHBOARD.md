# Dashboard Features

## Executive KPI Panel

- Subscriber Satisfaction Score (0-100%)
- VIP QoE Score (0-100%)
- Congestion Risk (0-100%)
- AI Confidence (0-100%)
- SLA Health (0-100%)
- Revenue Protection (USD)
- Predicted Mobility Pressure (0-100%)
- Monitoring Escalation Level (1-4)

---

## Live Telemetry Charts

- **RSRP Trend**: Signal strength over time (VIP vs Standard)
- **SINR Trend**: Signal quality with good/poor thresholds
- **Timing Advance**: Distance from cell (mass egress indicator)
- **PRB Utilization**: Congestion indicator with 80% threshold
- **Handover Success Rate**: Network stability metric
- **Congestion Heatmap**: PRB utilization matrix

---

## Mobility Digital Twin

- Taipei Arena marker (25.0516, 121.5500)
- Nanjing Fuxing MRT marker (25.0528, 121.5445)
- Subscriber dots colored by RSRP quality (green/orange/red)
- VIP subscribers shown larger
- Cell sector overlays (macro, small cell, DAS)
- YouBike station marker

---

## AI Multi-Agent Reasoning Console

Real-time chain-of-thought display:
```
[RAN Intelligence]
Signal cliff detected: RSRP drop 18dB
Underground transition likely
Handover storm: failure rate at 30%

[Mobility Intelligence]
Mass egress pattern confirmed
MRT congestion rising: YELLOW → RED
YouBike starvation: all 60 docks empty

[Context Intelligence]
Rainfall spiked to 12mm/hr
Walking propensity reduced 40%
Slip risk: MODERATE → HIGH

[Policy Validator]
VIP Priority Routing: APPROVED (92% confidence)
Secondary Load Balance: BLOCKED (loop detection)
  → Would cause neighboring cell PRB to exceed 85%

[Autonomous Action]
VIP Priority Routing Enabled
Expected KPI improvement: +23%
```

---

## Autonomous Actions

- **VIP Priority Routing**: Prioritize VIP traffic during congestion
- **Temporary Load Balancing**: Redistribute load to neighboring cells
- **Micro-cell Handover**: Steer to small cells for better coverage
- **Dynamic Slice Allocation**: Adjust network slicing for VIP
- **Small-cell Steering**: Direct to DAS for underground coverage

Each action includes:
- Confidence score (0–100%)
- Reasoning (why this action?)
- Expected KPI improvement (%)
- Policy approval status (APPROVED / BLOCKED)

# Scenario: Taipei Arena Concert Egress

**Event**: Power Station Concert
**Date**: May 15, 2026, 22:00
**Location**: Taipei Arena, Songshan District, Taipei
**Crowd Size**: ~1500 subscribers
**Weather**: Light rain (7.2 mm/hr), transitioning to heavy rain (12 mm/hr)

---

## Simulation Timeline

| Time | Phase | Key Events |
|------|-------|------------|
| 22:00 | **Pre-Egress** | Concert ending, crowd at arena. Normal RSRP (-88 to -92 dBm), PRB ~45% |
| 22:01 | **Weather Transition** | Rainfall spikes from 0 → 12 mm/hr. Walking propensity drops 40%. MRT preference increases |
| 22:02 | **Egress Begins** | Crowd moving toward MRT. TA increasing. RSRP degrading |
| 22:05 | **Signal Cliff** | RSRP drops >15dB as crowd enters MRT underground. Handover storm begins (30% failure rate) |
| 22:06 | **VIP Arc** | VIP subscriber underground, RSRP < -105 dBm. QoE degrading toward SLA breach |
| 22:07 | **MRT Overload** | PRB > 90% at MRT DAS cell. Congestion detected events fire. MRT exit capacity exceeded |
| 22:08 | **Anomaly Burst** | CQI drops to 2-3 across 20% of UEs for 10 ticks. `get_anomaly_report()` triggered |
| 22:10 | **YouBike Starvation** | All YouBike docks empty. Crowd backs up. Frustration index rises |
| 22:12 | **Secondary Congestion** | Load-balancing action causes neighboring cell to exceed PRB 85%. Policy loop detection fires |
| 22:15 | **Peak Congestion** | MRT congestion RED. AI triggers VIP Priority Routing. Policy validates ≥85% confidence |
| 22:20+ | **Dispersal** | Crowd dispersed. Congestion subsiding. KPIs return to normal |

---

## Seven Incident Arcs

| Arc | Trigger Condition | Agents Exercised | Autonomous Response |
|-----|-------------------|------------------|---------------------|
| **VIP Degradation** | VIP RSRP < -105 dBm at tick ~80 | RAN + Policy | VIP Priority Routing approved at 92% confidence |
| **MRT Overload Cascade** | PRB > 90% at MRT DAS cell | Mobility + Policy | Temporary Load Balancing triggered |
| **Weather Transition** | Rainfall spikes 0 → 12 mm/hr at tick ~50 | Context + Mobility | MRT capacity reallocation, slip risk alert |
| **Handover Storm** | Underground transition phase 0.65-0.80 | RAN | Micro-cell Handover, DAS steering |
| **Anomaly Burst** | 20% UEs with CQI 2-3 for 10 ticks | RAN (time-series) | `get_anomaly_report()` + diagnostic scan |
| **YouBike Starvation** | All 60 docks empty | Mobility | Crowd frustration index, MRT pressure alert |
| **Secondary Congestion** | Neighboring cell PRB > 85% from load-balance | Policy (loop detection) | Action blocked, alternative path proposed |

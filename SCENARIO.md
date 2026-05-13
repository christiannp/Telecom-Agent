# Scenario: Taipei Arena Concert Egress

**Event**: Power Station Concert
**Date**: May 15, 2026, 22:00
**Location**: Taipei Arena, Songshan District, Taipei
**Crowd Size**: ~1500 subscribers
**Weather**: Light rain (7.2 mm/hr), transitioning to heavy rain (12 mm/hr)

---

## Simulation Timeline

| Time | Tick | Key Events |
|------|------|------------|
| 22:00 | 0 | **Pre-Egress** — Concert ending, crowd at arena. Normal RSRP (-88 to -92 dBm), PRB ~45% |
| 22:01 | 6 | **Weather Transition** — Rainfall spikes 0 → 12 mm/hr. Walking propensity drops 40%. MRT preference increases |
| 22:02 | 12 | **Egress Begins** — Crowd moving toward MRT. TA rising. RSRP beginning to degrade |
| 22:04 | 24 | **Signal Cliff + Handover Storm** — RSRP drops >15dB as crowd enters MRT underground. 30% HO failure rate |
| 22:05 | 30 | **VIP Arc** — VIP subscribers underground, RSRP < -105 dBm. QoE degrading toward SLA breach |
| 22:06 | 36 | **MRT Overload** — PRB > 90% at MRT DAS cell. Congestion detected events fire. MRT exit capacity exceeded |
| 22:07 | 42 | **Anomaly Burst** — CQI drops to 2-3 across 20% of UEs. `get_anomaly_report()` triggered |
| 22:08 | 48 | **YouBike Starvation** — All 60 docks empty. Crowd backs up. Frustration index rises |
| 22:09 | 54 | **Secondary + Peak Congestion** — Load-balancing causes neighbor cell PRB > 85%. Policy loop detection fires. MRT RED. AI triggers VIP Priority Routing |
| 22:10 | 60 | **Dispersal** — Crowd dispersed. Congestion subsiding. KPIs return to normal |

---

## Seven Incident Arcs

| Arc | Trigger Condition | Tick Window | Agents Exercised | Autonomous Response |
|-----|-------------------|-------------|------------------|---------------------|
| **Weather Transition** | Rainfall spikes 0 → 12 mm/hr | 6–12 | Context + Mobility | MRT capacity reallocation, slip risk alert |
| **Handover Storm** | Underground transition phase 0.65–0.80 | 24–36 | RAN | Micro-cell Handover, DAS steering, 30% HO failure |
| **VIP Degradation** | VIP RSRP < -105 dBm underground | 30–36 | RAN + Policy | VIP Priority Routing approved at ≥85% confidence |
| **MRT Overload Cascade** | PRB > 90% at MRT DAS cell | 36–42 | Mobility + Policy | Temporary Load Balancing triggered |
| **Anomaly Burst** | 20% UEs with CQI 2–3 | 42–48 | RAN (time-series) | `get_anomaly_report()` + diagnostic scan |
| **YouBike Starvation** | All 60 docks empty | 48–60 | Mobility | Crowd frustration index, MRT pressure alert |
| **Secondary Congestion** | Neighboring cell PRB > 85% from load-balance | 54–60 | Policy (loop detection) | Action blocked, alternative path proposed |

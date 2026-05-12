# 📡 CovMo™ GenAI Telecom Intelligence Platform

> **Intent-Based RAN Optimization · Urban Mobility Intelligence · AI Autonomous Operations**

A production-grade AI-powered telecom operational intelligence platform demonstrating real-time network optimization using multi-agent AI orchestration. Built with Google ADK, LiteLLM, and Ollama.

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-Proprietary-yellow.svg)]()

![CovMo Platform](https://img.shields.io/badge/Status-Operational-brightgreen)

---

## Overview

**CovMo™** is an enterprise-grade telecom intelligence platform that simulates the **Taipei Arena Power Station Concert Egress** scenario (May 15, 2026, 22:00). The system demonstrates how AI can autonomously optimize telecom networks during mass egress events.

### Key Capabilities

- 🔴 **Real-time Level-2 RAN Telemetry** — RSRP, SINR, TA, PRB, CQI streaming at 500ms intervals
- 🤖 **Multi-Agent AI Orchestration** — 5 specialist agents coordinated via Google ADK
- 🗺️ **Urban Mobility Digital Twin** — Taipei Arena → Nanjing Fuxing MRT crowd simulation
- ⚡ **Autonomous Optimization** — Policy-validated AI actions with 85%+ confidence threshold
- 📊 **Subscriber-Level QoE Analytics** — VIP tracking with frustration index & degradation prediction
- 🌧️ **Weather-Aware Intelligence** — Rainfall impact on mobility patterns (7.2mm/hr scenario)
- 📈 **Executive KPI Dashboard** — Real-time business metrics with Plotly + Folium visualization
- 🔁 **Continuous Monitoring Loop** — Persistent alert escalation with escalating intervention levels
- 📽️ **Incident Replay** — Snapshot-based historical scrubbing at major incident boundaries
- 🔗 **Correlated Event Pipeline** — 6 unified scenario detectors cross-correlating RAN + Mobility + Context signals

### System Architecture

```
Streamlit Dashboard (8500) ──SSE──> FastAPI Server (8400) ──> Telemetry Streamer
                                             │
                                             ↓
                              AI Correlation & Analytics Layer
                                             │
                                             ↓
                             Google ADK Multi-Agent Orchestration
                                             │
                        ┌─────────┬──────────┼──────────┬─────────┐
                        │   RAN   │ Mobility │ Context  │ Policy  │
                        │  Agent  │  Agent   │  Agent   │  Agent  │
                        └─────────┴──────────┴──────────┴─────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.

### Multi-agent Design

[AGENTS.md](AGENTS.md) -> system details (5 agents + ADK tools)

---

## Dashboard UI

[DASHBOARD.md](DASHBOARD.md) -> Dashboard features, charts, maps, autonomous actions

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env file
cp .env.example .env
# Add your OLLAMA_API_KEY to .env

# 3. Run auto script
./run.sh
```

- **Dashboard**: http://localhost:8500
- **ADK Agents**: http://localhost:8080
- **API**: http://localhost:8400

See [GETTING_STARTED.md](GETTING_STARTED.md) for full instructions.

---

## Demo Scenario

The **Taipei Arena Power Station Concert Egress** (May 15, 2026, 22:00) simulates ~1,500 subscribers exiting a concert under heavy rain (0→12 mm/hr). The crowd funnels toward the Nanjing Fuxing MRT, creating a cascading network crisis across 7 incident arcs:

| Arc | Trigger | Autonomous Response |
|-----|---------|---------------------|
| **VIP Degradation** | VIP RSRP < −105 dBm underground | VIP Priority Routing approved at 92% confidence |
| **MRT Overload Cascade** | MRT DAS cell PRB > 90% | Temporary Load Balancing triggered |
| **Weather Transition** | Rain spikes 0→12 mm/hr at tick ~50 | MRT capacity reallocation + slip-risk alert |
| **Handover Storm** | Underground transition phase 0.65–0.80 | Micro-cell Handover + DAS steering |
| **Anomaly Burst** | 20% UEs with CQI 2–3 for 10 ticks | `get_anomaly_report()` + diagnostic scan |
| **YouBike Starvation** | All 60 docks empty | Frustration index + MRT pressure alert |
| **Secondary Congestion** | Neighboring cell PRB > 85% from load-balance | Action blocked, alternative path proposed |

All 7 arcs hit within a 20-minute window, stress-testing the multi-agent system under realistic cascading conditions — weather shifts, underground signal decay, VIP SLA breaches, and policy loop conflicts.

See [SCENARIO.md](SCENARIO.md) for full timeline and trigger details.

---

## Demo Questions

Users interact with the multi-agent system via natural language — queries are routed to the appropriate specialist agent (RAN, Mobility, Context, or Policy) and resolved autonomously. Example queries include:

| Domain | Example Questions |
|--------|-------------------|
| **Orchestrator** | *"What is happening right now in the network?"*, *"Should I be concerned in the next 5 minutes?"* |
| **RAN** | *"Show me active signal cliffs and handover failure rates"*, *"Generate a full anomaly report"* |
| **Mobility** | *"What is the MRT congestion status at each exit?"*, *"What is the current slip risk?"* |
| **Context** | *"How is weather affecting subscriber behavior?"*, *"Calculate walking propensity"* |
| **Policy** | *"Should I enable VIP Priority Routing now?"*, *"Would load balancing cause secondary congestion?"* |
| **VIP Analytics** | *"Show top 10 VIP subscribers by QoE degradation"*, *"Predict SLA breach in the next 5 minutes"* |

All autonomous actions require ≥85% confidence and ≥10% expected improvement before Policy agent approval.

See [USER_GUIDE.md](USER_GUIDE.md) for the full question library.

---

## Known Limitations

- **LLM Calls**: Agents defined but not actively called (requires Ollama API)
- **Weather API**: Uses mock data (Taiwan CWA integration ready but not active)
- **YouBike API**: Uses mock data (real API integration ready)
- **Historical Replay**: Not yet implemented
- **Multi-cell Handover**: Simplified model

---

## Roadmap

- [ ] Real Taiwan CWA API integration
- [ ] Real YouBike API integration
- [ ] Historical replay mode with timeline scrubbing
- [ ] Multi-cell handover visualization
- [ ] SON (Self-Organizing Network) optimization loop
- [ ] Subscriber journey replay
- [ ] Executive PDF report generation
- [ ] Prometheus metrics export
- [ ] Grafana dashboard integration
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests

---

## 🤝 Contributing

This is a proprietary demo project. For questions or collaboration inquiries, please contact the project maintainers.

---

## 📄 License

**Proprietary** — CovMo™ Telecom Intelligence Platform Demo

All rights reserved. This software is provided for demonstration purposes only.

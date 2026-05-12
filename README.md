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

---

## Architecture Summary

```
Streamlit Dashboard (8500) ──SSE──> FastAPI Server (8400) ──> Telemetry Streamer
                                                      │
                                                      ↓
                                        AI Correlation & Analytics Layer
                                                      │
                                                      ↓
                                        Google ADK Multi-Agent Orchestration
                                               │
                         ┌──────────┬──────────┼──────────┬──────────┐
                         │ RAN      │Mobility  │Context   │ Policy   │
                         │ Agent    │ Agent    │ Agent    │ Agent    │
                         └──────────┴──────────┴──────────┴──────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, tech stack, project structure |
| [AGENTS.md](AGENTS.md) | Multi-agent system details (5 agents + ADK tools) |
| [DASHBOARD.md](DASHBOARD.md) | Dashboard features, charts, maps, autonomous actions |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Installation, running, configuration, demo workflow |
| [SCENARIO.md](SCENARIO.md) | Taipei Arena concert egress scenario, 7 incident arcs |
| [USER_GUIDE.md](USER_GUIDE.md) | Example questions users can ask the multi-agent system |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Add your OLLAMA_API_KEY to .env

# 3. Run
./run.sh
```

- **Dashboard**: http://localhost:8500
- **ADK Agents**: http://localhost:8080
- **API**: http://localhost:8400

See [GETTING_STARTED.md](GETTING_STARTED.md) for full instructions.

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

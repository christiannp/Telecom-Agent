# Architecture

## System Overview

**CovMo™** is an enterprise-grade telecom intelligence platform that simulates the **Taipei Arena Power Station Concert Egress** scenario (May 15, 2026, 22:00). The system demonstrates how AI can autonomously optimize telecom networks during mass egress events.

---

## High-Level Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard (Port 8500)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Executive   │  │  Live RAN    │  │  Mobility    │             │
│  │  KPI Panel   │  │  Telemetry   │  │  Map         │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  AI Multi-   │  │  Autonomous  │  │  Subscriber  │             │
│  │  Agent       │  │  Actions     │  │  Analytics   │             │
│  │  Console     │  │  Panel       │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└───────────────────────────────────────────────────────────────────┘
                                ↓ SSE (Server-Sent Events)
┌───────────────────────────────────────────────────────────────────┐
│              FastAPI SSE Server (Port 8400)                       │
│  Endpoint: /stream-trace → Real-time telemetry events             │
└───────────────────────────────────────────────────────────────────┘
                                ↓
┌───────────────────────────────────────────────────────────────────┐
│              Telemetry Streamer (500ms ticks)                     │
│  • Generates 10-20 UE traces per tick                             │
│  • Simulates crowd egress (Arena → MRT)                           │
│  • Models signal degradation, congestion, handovers               │
│  • Injects 7 escalating incident arcs                             │
│  • Triggers correlated event detection                            │
└───────────────────────────────────────────────────────────────────┘
                                ↓
┌───────────────────────────────────────────────────────────────────┐
│         AI Correlation & Analytics Layer                          │
│  ┌──────────────────┐  ┌─────────────────��┐                       │
│  │ RAN Intelligence │  │ Mobility         │                       │
│  │ Engine           │  │ Intelligence     │                       │
│  │ • Signal cliffs  │  │ • MRT congestion │                       │
│  │ • Mass egress    │  │ • YouBike status │                       │
│  │ • Congestion     │  │ • Slip risk      │                       │
│  └──────────────────┘  └──────────────────┘                       │
│  ┌──────────────────┐  ┌──────────────────┐                       │
│  │ Context          │  │ Policy           │                       │
│  │ Intelligence     │  │ Validation       │                       │
│  │ • Weather impact │  │ • Action approval│                       │
│  │ • Walking        │  │ • SLA enforcement│                       │
│  │   propensity     │  │ • Governance     │                       │
│  └──────────────────┘  └──────────────────┘                       │
└───────────────────────────────────────────────────────────────────┘
                                ↓
┌───────────────────────────────────────────────────────────────────┐
│         Google ADK Multi-Agent Orchestration                      │
│                                                                   │
│              ┌─────────────────────────────┐                      │
│              │  Intent Orchestration Agent │                      │
│              │  (root_agent)               │                      │
│              │  • Coordinates sub-agents   │                      │
│              │  • Interprets user intent   │                      │
│              │  • Provides unified intel   │                      │
│              └─────────────────────────────┘                      │
│                          ↓                                        │
│     ┌────────────┬──────────┬───────────┬───────────┐             │
│     │            │          │           │           │             │
│     ▼            ▼          ▼           ▼           ▼             │
│┌────────┐   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │
││  RAN   │   │Mobility│  │Context │  │ Policy │  │ Tools  │        │
││ Agent  │   │ Agent  │  │ Agent  │  │ Agent  │  │ (7x)   │        │
│└────────┘   └────────┘  └────────┘  └────────┘  └────────┘        │
│                                                                   │
│  Model: Ollama Cloud (MiniMax M2.5 230B) via LiteLLM              │
└───────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
- **Python 3.13** — Core language
- **FastAPI** — SSE streaming server
- **Uvicorn** — ASGI server
- **AsyncIO** — Async telemetry generation
- **Pydantic** — Data validation
- **Google ADK** — Multi-agent orchestration
- **LiteLLM** — LLM abstraction layer
- **Ollama Cloud** — Gemma-4 31B model hosting

### Frontend
- **Streamlit** — Dashboard framework
- **Plotly** — Real-time charts (RSRP, SINR, TA, PRB, handover, heatmap)
- **Folium** — Interactive maps
- **PyDeck** — 3D geospatial visualization

### Data & Analytics
- **Pandas** — Time series analytics
- **NumPy** — Numerical computation
- **aiohttp** — Async HTTP client

---

## Project Structure

```
telecom_agent/
├── adk_apps/                   # ADK web app wrapper directory
├── agent.py                    # Google ADK entry point
├── agents.py                   # Multi-agent definitions (5 agents)
├── tools.py                    # ADK tool functions (7 tools)
├── models.py                   # Pydantic data models
├── config.py                   # Environment-based configuration
├── streamer.py                 # Async telemetry generator + incident arcs
├── adk_runner.py               # Async ADK agent runner
├── fastapi_server.py           # FastAPI SSE server
├── streamlit_app.py            # Streamlit dashboard entry
├── run.sh                      # Unified startup script
├── .env                        # Environment variables
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
│
├── services/                   # Business logic layer
│   ├── telemetry_service.py    # Telemetry state management
│   ├── ran_service.py          # RAN Intelligence Engine
│   ├── mobility_service.py     # Mobility Intelligence
│   ├── weather_service.py      # Weather awareness
│   └── policy_engine.py        # Policy validation + autonomous actions
│
├── ui/                         # Streamlit UI components
│   ├── dashboard.py            # Main dashboard
│   ├── components.py           # Reusable UI components
│   ├── charts.py               # Plotly chart renderers
│   └── maps.py                 # Folium/PyDeck maps
│
├── data/                       # Mock data files
│   ├── mock_cells.json         # Cell deployment (4 cells)
│   ├── mock_mrt.json           # MRT station (3 exits)
│   └── mock_youbike.json       # YouBike station
│
└── logs/                       # Policy decision logs
    └── policy_decisions.log
```
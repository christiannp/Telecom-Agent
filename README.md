# 📡 CovMo™ GenAI Telecom Intelligence Platform

> **Intent-Based RAN Optimization · Urban Mobility Intelligence · AI Autonomous Operations**

A production-grade AI-powered telecom operational intelligence platform demonstrating real-time network optimization using multi-agent AI orchestration. Built with Google ADK, LiteLLM, and Ollama.

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-Proprietary-yellow.svg)]()

![CovMo Platform](https://img.shields.io/badge/Status-Operational-brightgreen)

---

## 🎯 Overview

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

## 🏗️ Architecture

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
│  ┌──────────────────┐  ┌──────────────────┐                       │
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

## 🤖 Multi-Agent System

### 1. **Intent Orchestration Agent** (`root_agent`)
**Role**: Primary AI interface coordinating all specialist agents

**Capabilities**:
- Interprets user queries ("Analyze concert exit", "Show VIP congestion risk")
- Coordinates RAN, Mobility, Context, and Policy agents
- Provides unified operational intelligence
- Explains AI reasoning with confidence scores

**Tools**: All 7 ADK tools (RAN state, mobility state, KPI dashboard, subscriber info, VIP info, action validation, action execution)

### 2. **RAN Intelligence Agent** (`ran_intelligence_agent`)
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

### 3. **Mobility Intelligence Agent** (`mobility_intelligence_agent`)
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

### 4. **Context Intelligence Agent** (`context_intelligence_agent`)
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

### 5. **Policy Validation Agent** (`policy_validation_agent`)
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

## 📊 Dashboard Features

### Executive KPI Panel
- Subscriber Satisfaction Score (0-100%)
- VIP QoE Score (0-100%)
- Congestion Risk (0-100%)
- AI Confidence (0-100%)
- SLA Health (0-100%)
- Revenue Protection (USD)
- Predicted Mobility Pressure (0-100%)
- Monitoring Escalation Level (1-4)

### Live Telemetry Charts
- **RSRP Trend**: Signal strength over time (VIP vs Standard)
- **SINR Trend**: Signal quality with good/poor thresholds
- **Timing Advance**: Distance from cell (mass egress indicator)
- **PRB Utilization**: Congestion indicator with 80% threshold
- **Handover Success Rate**: Network stability metric
- **Congestion Heatmap**: PRB utilization matrix

### Mobility Digital Twin
- Taipei Arena marker (25.0516, 121.5500)
- Nanjing Fuxing MRT marker (25.0528, 121.5445)
- Subscriber dots colored by RSRP quality (green/orange/red)
- VIP subscribers shown larger
- Cell sector overlays (macro, small cell, DAS)
- YouBike station marker

### AI Multi-Agent Reasoning Console
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

### Autonomous Actions
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

---

## 🛠️ Technology Stack

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

## 📁 Project Structure

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

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (tested on 3.13)
- **Ollama API Key** (from https://ollama.com)
- **macOS / Linux** (Windows via WSL)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd telecom_agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OLLAMA_API_KEY
```

### Running the Platform

**Option A: Unified Startup (Recommended)**

```bash
chmod +x run.sh
./run.sh
```

**Option B: Manual Startup**

Terminal 1 — FastAPI SSE Server:
```bash
source venv/bin/activate
export $(cat .env | xargs)
python fastapi_server.py
```

Terminal 2 — Streamlit Dashboard:
```bash
source venv/bin/activate
export $(cat .env | xargs)
streamlit run streamlit_app.py --server.port 8500
```

Terminal 3 — ADK Multi-Agent Web UI:
```bash
source venv/bin/activate
export $(cat .env | xargs)
adk web --port 8080 --allow_origins "*" adk_apps
```

### Access the Platform

- **Dashboard**: http://localhost:8500 — Live KPI charts, mobility map, AI console
- **ADK Agents**: http://localhost:8080 — Select `telecom_agent` to chat with the multi-agent system
- **API**: http://localhost:8400 — SSE stream `/stream-trace`, health `/health`

The dashboard auto-connects to the SSE stream when the API is ready.

## 🔧 Configuration

Edit `.env` or `config.py`:

```bash
# LLM Configuration
OLLAMA_API_KEY=your_key_here
OLLAMA_API_BASE=https://ollama.com/v1
LLM_MODEL=ollama_chat/minimax-m2.5:cloud

# Simulation Parameters
TELEMETRY_INTERVAL_MS=500        # Telemetry tick interval
SIMULATION_DENSITY=15            # UEs per tick
UI_REFRESH_RATE=1                # Dashboard refresh (seconds)

# RAN Thresholds
CONGESTION_THRESHOLD_PRB=80      # PRB % for congestion alert
CONFIDENCE_THRESHOLD=85          # Min confidence for autonomous action
MASS_EGRESS_TA_PCT=0.70          # 70% subscribers with increasing TA
SIGNAL_CLIFF_DB=15.0             # RSRP drop threshold

# Weather
ENABLE_WEATHER=true
WEATHER_FALLBACK_RAIN_MM_HR=0.0

# Ports
API_PORT=8400
STREAMLIT_PORT=8500
ADK_PORT=8080
```

---

## 🎮 Demo Workflow

1. **Start Streaming**: The dashboard starts the SSE stream automatically
2. **Watch Telemetry**: Live RSRP, SINR, TA, PRB charts update every second
3. **Monitor Mobility**: Map shows crowd movement from Taipei Arena → MRT
4. **AI Reasoning**: Multi-agent console displays real-time operational intelligence
5. **Autonomous Actions**: Policy-validated AI actions appear as they're triggered
6. **VIP Analytics**: Track individual VIP subscriber QoE degradation
7. **Continuous Monitoring**: Escalation levels appear after persistent alerts
8. **Incident Replay**: Scrub through past snapshots at major incident boundaries
9. **Correlated Events**: Unified scenario inferences displayed in SSE payload

### Expected Behavior

- **Tick 1-50**: Crowd at arena, RSRP ~-90dBm, TA ~10-15, PRB ~45%
- **Tick 50-100**: Crowd moving, RSRP degrading, TA increasing, PRB rising
- **Tick 100-200**: Crowd at MRT underground, RSRP ~-102dBm, TA ~35, PRB ~75%
- **Signal Cliff**: Detected when RSRP drops >15dB with stable TA
- **Mass Egress**: Detected when 70%+ subscribers show increasing TA
- **MRT Congestion**: Escalates from GREEN → YELLOW → RED
- **VIP Arc (~tick 80)**: VIP subscriber RSRP drops below -105 dBm; QoE degrades; SLA breach triggers
- **Weather Transition (~tick 50)**: Rainfall spikes 0 → 12 mm/hr; walking propensity drops 40%; MRT pressure doubles
- **Handover Storm (0.65 < phase < 0.80)**: Handover failure rate spikes to 30%
- **Anomaly Burst**: CQI drops to 2-3 across 20% of UEs for 10 ticks

---

## 🎯 Scenario: Taipei Arena Concert Egress — Full Incident Arcs

**Event**: Power Station Concert
**Date**: May 15, 2026, 22:00
**Location**: Taipei Arena, Songshan District, Taipei
**Crowd Size**: ~1500 subscribers
**Weather**: Light rain (7.2 mm/hr), transitioning to heavy rain (12 mm/hr)

### Simulation Timeline

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

### Seven Incident Arcs

| Arc | Trigger Condition | Agents Exercised | Autonomous Response |
|-----|-------------------|------------------|---------------------|
| **VIP Degradation** | VIP RSRP < -105 dBm at tick ~80 | RAN + Policy | VIP Priority Routing approved at 92% confidence |
| **MRT Overload Cascade** | PRB > 90% at MRT DAS cell | Mobility + Policy | Temporary Load Balancing triggered |
| **Weather Transition** | Rainfall spikes 0 → 12 mm/hr at tick ~50 | Context + Mobility | MRT capacity reallocation, slip risk alert |
| **Handover Storm** | Underground transition phase 0.65-0.80 | RAN | Micro-cell Handover, DAS steering |
| **Anomaly Burst** | 20% UEs with CQI 2-3 for 10 ticks | RAN (time-series) | `get_anomaly_report()` + diagnostic scan |
| **YouBike Starvation** | All 60 docks empty | Mobility | Crowd frustration index, MRT pressure alert |
| **Secondary Congestion** | Neighboring cell PRB > 85% from load-balance | Policy (loop detection) | Action blocked, alternative path proposed |

---

## 💬 Questions Users Can Ask

The ADK multi-agent system accepts natural-language queries and routes them to the appropriate specialist agent. Below are example questions organized by domain.

### General / Orchestrator

- **"What is happening right now in the network?"**
  → Orchestrator coordinates all agents and returns a unified situational summary with confidence scores.

- **"Give me a complete status report of the Taipei Arena scenario."**
  → Orchestrator aggregates RAN, mobility, weather, and policy state into a single briefing.

- **"Should I be concerned about anything in the next 5 minutes?"**
  → Orchestrator invokes all agents to predict near-term risks and prioritizes by SLA impact.

- **"Summarize the AI reasoning behind recent autonomous actions."**
  → Orchestrator retrieves and explains the chain-of-thought from each agent that contributed to recent actions.

### RAN Intelligence

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

### Mobility Intelligence

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

### Context Intelligence

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

### Policy Validation

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

### Subscriber & VIP Analytics

- **"Show me the top 10 VIP subscribers by QoE degradation."**
  → Returns VIP subscribers sorted by largest QoE drop, with current RSRP, SINR, and predicted SLA breach time.

- **"Which subscribers are experiencing the worst signal quality?"**
  → Returns subscribers with lowest RSRP/SINR, grouped by location (arena, transit, MRT underground).

- **"What is the overall subscriber satisfaction score?"**
  → Returns the executive KPI: Subscriber Satisfaction Score (0–100%) with trend over the last 50 ticks.

- **"Predict which VIP subscribers will breach SLA in the next 5 minutes."**
  → Uses RAN + mobility trend analysis to predict VIP QoE drop below 80 and estimates time-to-breach.

### KPI & Executive Dashboard

- **"What are the current executive KPIs?"**
  → Returns Subscriber Satisfaction, VIP QoE, Congestion Risk, AI Confidence, SLA Health, Revenue Protection (USD), and Mobility Pressure.

- **"How much revenue has been protected by autonomous actions today?"**
  → Policy agent calculates revenue protected by preventing VIP SLA breaches.

- **"Show me the KPI trend chart for the last 30 minutes."**
  → Returns Plotly chart data for all executive KPIs over the specified window.

- **"What is the AI confidence level for the current operational state?"**
  → Returns the AI Confidence KPI (0–100%) based on model agreement across all active agents.

### Correlated Events & Scenario Detection

- **"What correlated scenarios are active right now?"**
  → Returns output from `correlate_events()`: the 6 unified scenario detectors (signal cliff + underground transition, mass egress + MRT overload, weather shift + walking propensity, etc.).

- **"Are there any cross-domain anomalies that suggest a cascading failure?"**
  → Correlation pipeline detects when RAN degradation + mobility congestion + weather shift occur simultaneously and alerts.

- **"Show me the monitoring escalation level."**
  → Returns current escalation level (1–4) from `run_monitoring_check()`: INFO → WARN → ELEVATED → CRITICAL.

### Incident Replay

- **"Save a snapshot of the current state."**
  → Triggers `save_snapshot()` at the current tick for later replay.

- **"Replay the VIP degradation incident from tick 70 to 90."**
  → Loads the snapshot saved at tick ~80 (first RED alert / VIP SLA breach) and replays telemetry in scrubbed mode.

- **"What happened during the handover storm incident?"**
  → Replays the incident arc captured between phases 0.65–0.80, showing the RAN agent's reasoning and actions taken.

---

## 🚧 Known Limitations

- **LLM Calls**: Agents defined but not actively called (requires Ollama API)
- **Weather API**: Uses mock data (Taiwan CWA integration ready but not active)
- **YouBike API**: Uses mock data (real API integration ready)
- **Historical Replay**: Not yet implemented
- **Multi-cell Handover**: Simplified model

---

## 🛣️ Roadmap

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
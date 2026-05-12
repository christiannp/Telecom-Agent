# Getting Started

## Prerequisites

- **Python 3.11+** (tested on 3.13)
- **Ollama API Key** (from https://ollama.com)
- **macOS / Linux** (Windows via WSL)

---

## Installation

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

---

## Running the Platform

### Option A: Unified Startup (Recommended)

```bash
chmod +x run.sh
./run.sh
```

### Option B: Manual Startup

**Terminal 1 — FastAPI SSE Server:**
```bash
source venv/bin/activate
export $(cat .env | xargs)
python fastapi_server.py
```

**Terminal 2 — Streamlit Dashboard:**
```bash
source venv/bin/activate
export $(cat .env | xargs)
streamlit run streamlit_app.py --server.port 8500
```

**Terminal 3 — ADK Multi-Agent Web UI:**
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

---

## Configuration

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

## Demo Workflow

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

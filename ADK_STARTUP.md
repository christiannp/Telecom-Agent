# 🤖 Starting the ADK Multi-Agent System

The CovMo platform has **5 AI agents** built with Google ADK. Here's how to start them:

---

## Quick Start (3 Steps)

### 1. Start FastAPI SSE Server (Port 8400)

```bash
cd telecom_agent
source ../venv/bin/activate
export $(cat .env | xargs)
python fastapi_server.py
```

**Expected output:**
```
INFO:     Started server process [...]
INFO:     Uvicorn running on http://0.0.0.0:8400
```

---

### 2. Start Streamlit Dashboard (Port 8500)

**New terminal:**
```bash
cd telecom_agent
source ../venv/bin/activate
export $(cat .env | xargs)
streamlit run streamlit_app.py --server.port 8500
```

**Expected output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8500
```

**Open browser:** http://localhost:8500  
The dashboard auto-connects to the SSE stream when the API is ready.

---

### 3. Start ADK Multi-Agent Web UI (Port 8080)

**New terminal:**
```bash
cd telecom_agent
source ../venv/bin/activate
export $(cat .env | xargs)
adk web --port 8080 --allow_origins "*" adk_apps
```

**Expected output:**
```
+-----------------------------------------------------------------------------+
| ADK Web Server started                                                      |
| For local testing, access at http://127.0.0.1:8080.                         |
+-----------------------------------------------------------------------------+
```

**Open browser:** http://localhost:8080

In the ADK app selector, choose **`telecom_agent`**. The app contains
`root_agent` plus the four specialist sub-agents.

---

## Alternative: Use the Unified Startup Script

```bash
cd telecom_agent
chmod +x run.sh
./run.sh
```

This starts **FastAPI (8400) + Streamlit (8500) + ADK Web (8080)** together.
If you prefer to start ADK manually in a separate terminal:

```bash
cd telecom_agent
source ../venv/bin/activate
export $(cat .env | xargs)
adk web --port 8080 --allow_origins "*" adk_apps
```

---

## What Each Port Does

| Port | Service | Purpose |
|------|---------|---------|
| **8400** | FastAPI SSE | Real-time telemetry streaming (`/stream-trace`) |
| **8500** | Streamlit | Live operational dashboard with charts + maps |
| **8080** | ADK Web UI | Multi-agent chat interface for querying agents |

---

## Using the ADK Agents

Once ADK web is running at **http://localhost:8080**, you can interact with the agents:

Select the **`telecom_agent`** app first. ADK lists apps at the top level;
`root_agent` coordinates the specialist agents inside that app.

### Available Agents

1. **`root_agent`** — Intent Orchestration Agent (coordinates all sub-agents)
2. **`ran_intelligence_agent`** — RAN Intelligence (signal cliffs, congestion)
3. **`mobility_intelligence_agent`** — Mobility Intelligence (MRT, YouBike)
4. **`context_intelligence_agent`** — Context Intelligence (weather, slip risk)
5. **`policy_validation_agent`** — Policy Validation (action approval)

### Example Queries

Try these in the ADK web chat:

```
Analyze the Power Station concert exit

Show VIP congestion risk near Exit 2

Why did premium user QoE degrade?

Predict MRT overload in 10 minutes

What's the current RAN status?

Get subscriber info for VIP_001

Validate this autonomous action: VIP Priority Routing with 92% confidence
```

---

## Agent Tools Available

Each agent has access to these 7 tools:

1. **`get_ran_state()`** — RAN metrics and alerts
2. **`get_mobility_)`** — MRT congestion, YouBike, mass egress
3. **`get_weather_state()`** — Weather impact on mobility
4. **`get_kpi_dashboard()`** — Executive KPI snapshot
5. **`get_subscriber_info(ue_id)`** — Individual subscriber details
6. **`get_all_vip_info()`** — All VIP subscriber metrics
7. **`validate_autonomous_action(action_json)`** — Policy validation

---

## Troubleshooting

### ADK web won't start

**Error:** `Agent not found` or `No agents loaded`

**Fix:** Ensure you're running `adk web` from the `telecom_agent/` directory and pointing it at the ADK app wrapper:
```bash
cd telecom_agent
adk web --port 8080 adk_apps
```

ADK 1.33 expects an agents directory whose child folders contain `agent.py`.
The `adk_apps` wrapper exposes this project as the `telecom_agent` app.

---

### Port already in use

**Error:** `Address already in use`

**Fix:** Kill existing processes:
```bash
# Kill FastAPI
lsof -ti:8400 | xargs kill -9

# Kill Streamlit
lsof -ti:8500 | xargs kill -9

# Kill ADK
lsof -ti:8080 | xargs kill -9
```

---

### Ollama API key not found

**Error:** `OLLAMA_API_KEY not set`

**Fix:** Ensure `.env` exists and is loaded:
```bash
cd telecom_agent
cat .env  # Should show OLLAMA_API_KEY=...
export $(cat .env | xargs)
echo $OLLAMA_API_KEY  # Should print your key
```

---

## Architecture Recap

```
┌─────────────────────────────────────────────────────────────┐
│  Browser: http://localhost:8500 (Streamlit Dashboard)      │
│  • Live telemetry charts                                   │
│  • Mobility map                                            │
│  • AI reasoning console                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓ polls SSE
┌─────────────────────────────────────────────────────────────┐
│  FastAPI: http://localhost:8400                            │
│  • /stream-trace → SSE telemetry stream                    │
│  • /health → health check                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓ uses
┌─────────────────────────────────────────────────────────────┐
│  Telemetry Streamer (streamer.py)                          │
│  • Generates 60 UE traces every 500ms                      │
│  • Calls RAN/Mobility/Weather services                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Browser: http://localhost:8080 (ADK Web UI)               │
│  • Chat with agents                                        │
│  • Query operational intelligence                          │
│  • Validate autonomous actions                             │
└─────────────────────────────────────────────────────────────┘
                          ↓ invokes
┌─────────────────────────────────────────────────────────────┐
│  Google ADK Multi-Agent System (agents.py)                 │
│  • root_agent (Intent Orchestration)                       │
│  • ran_intelligence_agent                                  │
│  • mobility_intelligence_agent                             │
│  • context_intelligence_agent                              │
│  • policy_validation_agent                                 │
│                                                             │
│  Model: Ollama Cloud (Gemma-4 31B) via LiteLLM             │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

**3 services run independently:**

1. **FastAPI (8400)** — Telemetry streg backend
2. **Streamlit (8500)** — al dashboard frontend
3. **ADK Web (8080)** — Multi-agent chat interface

**Start order:**
1. FastAPI first (provides data)
2. Streamlit second (consumes data)
3. ADK third (queries agents)

**All 3 can run simultaneously** — they don't conflict because they use different ports.

---

**Quick test:**
```bash
# Terminal 1
cd telecom_agent && source ../venv/bin/activate && export $(cat .env | xargs) && python fastapi_server.py

# Terminal 2
cd telecom_agent && source ../venv/bin/activate && export $(cat .env | xargs) && streamlit run streamlit_app.py --server.port 8500

# Terminal 3
cd telecom_agent && source ../venv/bin/activate && export $(cat .env | xargs) && adk web --port 8080 --allow_origins "*" adk_apps
```

Then open:
- http://localhost:8500 (Dashboard)
- http://localhost:8080 (Agents)

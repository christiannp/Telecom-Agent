#!/bin/bash
# CovMo Telecom Intelligence Platform — Unified Startup Script
#
# Starts all 3 services in one command:
#   1. FastAPI SSE Server   → http://localhost:8400
#   2. Streamlit Dashboard  → http://localhost:8500
#   3. ADK Multi-Agent Web → http://localhost:8080

set -e

cd "$(dirname "$0")"
source ../venv/bin/activate

# Load environment variables
export $(cat .env | xargs)

# ── Helper: Kill process on port ─────────────────────────────
kill_port() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "   🛑 Port $port in use — killing: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# ── Helper: Wait for port to be ready ────────────────────────
wait_port() {
    local port=$1
    local name=$2
    for i in {1..10}; do
        if lsof -i :$port 2>/dev/null | grep -q LISTEN; then
            echo "   ✓ $name ready on port $port"
            return 0
        fi
        sleep 1
    done
    echo "   ⚠️  $name did not start on port $port"
    return 1
}

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       📡 CovMo™ Telecom Intelligence Platform               ║"
echo "║        Taipei Arena Concert Egress — May 15, 2026          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Cleanup any stale processes ───────────────────────────────
echo "🔍 Checking for stale processes..."
kill_port 8400
kill_port 8500
kill_port 8080
echo ""

# ── 1. FastAPI SSE Server ──────────────────────────────────────
echo "📡 [1/3] Starting FastAPI SSE Server on http://localhost:8400"
python fastapi_server.py &
FASTAPI_PID=$!
echo "   ✓ FastAPI PID: $FASTAPI_PID"
wait_port 8400 "FastAPI"

# ── 2. Streamlit Dashboard ────────────────────────────────────
echo ""
echo "🖥️  [2/3] Starting Streamlit Dashboard on http://localhost:8500"
streamlit run streamlit_app.py \
    --server.port 8500 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --server.runOnSave false \
    --server.enableCORS false \
    --server.enableXsrfProtection true \
    > /dev/null 2>&1 &
STREAMLIT_PID=$!
echo "   ✓ Streamlit PID: $STREAMLIT_PID"
wait_port 8500 "Streamlit"

# ── 3. ADK Multi-Agent Web UI ─────────────────────────────────
echo ""
echo "🤖 [3/3] Starting ADK Multi-Agent Web UI on http://localhost:8080"
adk web \
    --port 8080 \
    --allow_origins "*" \
    --host 127.0.0.1 \
    --no-reload \
    adk_apps \
    > /dev/null 2>&1 &
ADK_PID=$!
echo "   ✓ ADK Web PID: $ADK_PID"
wait_port 8080 "ADK Web UI"

# ── Final Status ───────────────────────────────────────────────
sleep 1
echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "   ✅ ALL SERVICES STARTED SUCCESSFULLY"
echo "══════════════════════════════════════════════════════════════════"
echo ""
echo "   📊 Dashboard:    http://localhost:8500"
echo "      • Live KPI panel, RSRP/SINR/TA/PRB charts"
echo "      • Mobility map (Taipei Arena → MRT)"
echo "      • AI reasoning console + autonomous actions"
echo "      • Auto-connects to the SSE telemetry stream"
echo ""
echo "   🤖 ADK Agents:  http://localhost:8080"
echo "      • Chat with 5 AI agents"
echo "      • Try: 'Analyze the concert exit'"
echo "             'Show VIP congestion risk near Exit 2'"
echo "             'Why did premium user QoE degrade?'"
echo ""
echo "   📡 API:         http://localhost:8400"
echo "      • SSE stream:  /stream-trace"
echo "      • Health:      /health"
echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "   Press Ctrl+C to stop all services"
echo "══════════════════════════════════════════════════════════════════"
echo ""

# ── Keep alive + Cleanup ───────────────────────────────────────
_cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $STREAMLIT_PID 2>/dev/null || true
    kill $ADK_PID 2>/dev/null || true
    kill $FASTAPI_PID 2>/dev/null || true
    echo "   ✅ All services stopped"
}

trap _cleanup SIGINT SIGTERM EXIT
wait $FASTAPI_PID $STREAMLIT_PID $ADK_PID

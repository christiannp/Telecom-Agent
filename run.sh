#!/bin/bash
# CovMo Telecom Intelligence Platform — Startup Script

set -e

cd "$(dirname "$0")"
source ../venv/bin/activate

# Load environment
export $(cat .env | xargs)

echo "🚀 Starting CovMo Telecom Intelligence Platform..."
echo ""
echo "📡 FastAPI SSE Server: http://localhost:8000"
echo "🖥️  Streamlit Dashboard: http://localhost:8501"
echo ""

# Start FastAPI in background
python fastapi_server.py &
FASTAPI_PID=$!

# Wait for FastAPI to start
sleep 2

# Start Streamlit
streamlit run streamlit_app.py --server.port 8501

# Cleanup on exit
trap "kill $FASTAPI_PID" EXIT

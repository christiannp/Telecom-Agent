"""
ADK Runner for CovMo Telecom Intelligence Platform.

Run this AFTER starting fastapi_server.py and streamlit_app.py
to activate the multi-agent AI orchestration.

Usage:
    python adk_runner.py

This starts the ADK web interface on port 8080.
Open http://localhost:8080 to interact with the agents.
"""
from __future__ import annotations

import os, sys

# Ensure the project root is in the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from dotenv import load_dotenv

# Load .env from telecom_agent dir
_env_path = os.path.join(project_root, ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path, override=True)
else:
    # Try parent dir
    _env_path = os.path.join(os.path.dirname(project_root), ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path, override=True)

# Suppress uvicorn startup spam from sub-dependencies
import logging
logging.getLogger("uvicorn.access").disabled = True
logging.getLogger("uvicorn.error").disabled = True

if __name__ == "__main__":
    import subprocess

    print("=" * 60)
    print("🤖 CovMo™ — ADK Multi-Agent Orchestration")
    print("=" * 60)
    print()
    print("Prerequisites:")
    print("  1. Start FastAPI SSE:  python fastapi_server.py")
    print("  2. Start Dashboard:    streamlit run streamlit_app.py")
    print()
    print("Starting ADK web server on http://localhost:8080")
    print()

    # Set up LiteLLM proxy in background
    lite_llm_proc = None
    try:
        print("[1/2] Starting LiteLLM proxy...")
        lite_llm_proc = subprocess.Popen(
            ["python", "-m", "litellm", "--config", "config.yaml"],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"  ⚠ LiteLLM proxy start skipped: {e}")

    # Give LiteLLM a moment to bind its port
    import time
    time.sleep(2)

    # Start ADK web
    print("[2/2] Starting ADK web server...")
    print()
    print("=" * 60)
    print("Once running, open your browser to:")
    print("  👉 http://localhost:8080")
    print()
    print("Agents available:")
    print("  📡 root_agent       — Intent Orchestration (coordinates all)")
    print("  📡 ran_intelligence — RAN analysis (signal cliffs, congestion)")
    print("  📡 mobility_intel   — Mobility analysis (MRT, YouBike)")
    print("  📡 context_intel    — Context analysis (weather, slip risk)")
    print("  📡 policy_validation— Policy governance (action approval)")
    print()
    print("Example queries:")
    print('  "Analyze the concert exit"')
    print('  "Show VIP congestion risk near Exit 2"')
    print('  "Predict MRT overload in 10 minutes"')
    print('  "Why did premium user QoE degrade?"')
    print("=" * 60)
    print()

    result = subprocess.run(
        ["python", "-m", "google.adk.cli.fast_api", "web",
         "--port", "8080",
         "--agent_path", project_root,
         "--allowed_origin", "*"],
        cwd=project_root,
    )

    # Cleanup
    if lite_llm_proc:
        lite_llm_proc.terminate()

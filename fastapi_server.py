"""
FastAPI SSE server for CovMo Telecom Intelligence Platform.

Run with: python fastapi_server.py
"""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

from streamer import stream_telemetry
from config import API_PORT


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="CovMo Telecom Intelligence Platform API",
    description="SSE telemetry streaming endpoint",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "platform": "CovMo Telecom Intelligence Platform",
        "version": "1.0.0",
        "scenario": "Taipei Arena Power Station Concert Egress",
        "date": "May 15, 2026 22:00",
        "status": "operational",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/stream-trace")
async def stream_trace(request: Request):
    """
    Server-Sent Events endpoint for real-time telemetry streaming.
    """
    async def event_generator():
        try:
            async for payload in stream_telemetry():
                payload_str = json.dumps(payload, default=str)
                yield f"data: {payload_str}\n\n"
        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")

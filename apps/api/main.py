#!/usr/bin/env python3
"""
main.py --- FastAPI application entrypoint for the agentflow orchestrator API

Contains:
    create_app(): builds and configures the FastAPI application
    app: module-level ASGI application instance
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from apps.api.config import get_settings
from apps.api.trace_hub import TraceHub


def create_app() -> FastAPI:
    """Builds and configures the FastAPI application.

    Returns:
        app: Configured FastAPI application instance.
    """
    settings = get_settings()
    app = FastAPI(title="agentflow", version=settings.app_version)
    hub = TraceHub()

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Returns service health status."""
        return {"status": "ok"}

    @app.websocket("/ws/traces")
    async def trace_stream(socket: WebSocket, run_id: str = "default") -> None:
        """Streams live orchestration trace events to console clients."""
        await hub.register(run_id, socket)
        try:
            while True:
                await socket.receive_text()
        except WebSocketDisconnect:
            hub.discard(run_id, socket)

    return app


app = create_app()

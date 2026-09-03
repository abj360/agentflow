#!/usr/bin/env python3
"""
main.py --- FastAPI application entrypoint for the agentflow orchestrator API

Contains:
    create_app(): builds and configures the FastAPI application
    app: module-level ASGI application instance
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from apps.api.approvals.routes import router as approvals_router
from apps.api.audit.routes import router as audit_router
from apps.api.config import get_settings
from apps.api.middleware.rate_limit import RateLimitMiddleware
from apps.api.observability.metrics import metrics_endpoint
from apps.api.observability.tracing import setup_tracing
from apps.api.trace_hub import TraceHub


def create_app() -> FastAPI:
    """Builds and configures the FastAPI application.

    Returns:
        app: Configured FastAPI application instance.
    """
    settings = get_settings()
    app = FastAPI(title="agentflow", version=settings.app_version)
    hub = TraceHub()
    if settings.otel_exporter_otlp_endpoint:
        setup_tracing(app, service_name=settings.otel_service_name)
    app.include_router(audit_router)
    app.include_router(approvals_router)
    app.add_route("/metrics", metrics_endpoint)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Returns service health status.

        Returns:
            status: Health payload reporting the service is up.
        """
        return {"status": "ok"}

    @app.websocket("/ws/traces")
    async def trace_stream(socket: WebSocket, run_id: str = "default") -> None:
        """Streams live orchestration trace events to console clients.

        Args:
            socket: The viewer's WebSocket connection.
            run_id: Run whose trace events the viewer wants to stream.
        """
        if not await hub.register(run_id, socket):
            return
        try:
            while True:
                await socket.receive_text()
        except WebSocketDisconnect:
            hub.discard(run_id, socket)

    return app


app = create_app()

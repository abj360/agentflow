#!/usr/bin/env python3
"""
main.py --- FastAPI application entrypoint for the agentflow orchestrator API

Contains:
    StartRunRequest: body accepted when a caller starts a run
    create_app(): builds and configures the FastAPI application
    app: module-level ASGI application instance
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from apps.api.approvals.routes import router as approvals_router
from apps.api.audit.routes import router as audit_router
from apps.api.config import get_settings
from apps.api.middleware.rate_limit import RateLimitMiddleware
from apps.api.observability.metrics import metrics_endpoint
from apps.api.observability.tracing import setup_tracing
from apps.api.orchestration.graph_events import (
    node_status_changed,
    traced_events_for_plan,
)
from apps.api.orchestration.loop import run_session
from apps.api.orchestration.task_planner import TaskPlanner, TaskStatus
from apps.api.trace_hub import TraceHub


class StartRunRequest(BaseModel):
    """Represents the body accepted when a caller starts a run.

    Attributes:
        task: The work the planner should decompose into a task graph.
    """

    task: str = Field(min_length=1)


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
        CORSMiddleware,
        allow_origins=settings.allowed_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
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

    @app.post("/runs/{run_id}")
    async def start_run(run_id: str, body: StartRunRequest) -> dict[str, str | int]:
        """Starts one run and streams its task graph to that run's viewers.

        Args:
            run_id: Run the caller wants the graph streamed under.
            body: The task the planner should decompose.

        Returns:
            summary: The run's final status and how many tasks it planned.
        """
        planned = TaskPlanner().plan(body.task)
        if not planned:
            raise HTTPException(status_code=422, detail="task decomposed into no plannable work")
        await hub.broadcast_batch(run_id, traced_events_for_plan(run_id, planned))
        transitions: list[tuple[str, TaskStatus]] = []

        def record(task_id: str, status: TaskStatus) -> None:
            """Records one status transition for the batch sent after the run.

            Args:
                task_id: Task whose status moved.
                status: Lifecycle state the task moved into.
            """
            transitions.append((task_id, status))

        result = await run_session(run_id, body.task, on_status=record)
        await hub.broadcast_batch(
            run_id,
            [node_status_changed(task_id, status) for task_id, status in transitions],
        )
        await hub.broadcast(
            run_id,
            {
                "kind": "run_finished",
                "role": "orchestrator",
                "payload": {"status": result["status"], "tasks": len(planned)},
            },
        )
        return {"status": str(result["status"]), "tasks": len(planned)}

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

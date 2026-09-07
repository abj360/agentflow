#!/usr/bin/env python3
"""
main.py --- FastAPI application entrypoint for the agentflow orchestrator API

Contains:
    NO_PROVIDER: what the coordinator says when it has no model to think with
    StartRunRequest: body accepted when a caller starts a run
    ProviderRequest: body accepted when a caller configures the model provider
    ModelRequest: body accepted when a caller pins a different model
    TurnResult: what one turn of the conversation did with the run
    run_answer(): renders a finished run as the reply the orchestrator sends back
    stopped_early(): says which tasks a run did not get to, and why
    datastore_unavailable(): turns an unreachable datastore into a readable 503
    create_app(): builds and configures the FastAPI application
    app: module-level ASGI application instance
"""

import asyncio
import logging
from collections.abc import Mapping, Sequence

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from apps.api.approvals.routes import router as approvals_router
from apps.api.audit.routes import router as audit_router
from apps.api.config import get_settings
from apps.api.db import DatastoreUnavailable
from apps.api.middleware.rate_limit import RateLimitMiddleware
from apps.api.observability.metrics import metrics_endpoint
from apps.api.observability.tracing import setup_tracing
from apps.api.orchestration.agents import run_task
from apps.api.orchestration.conversations import Conversations
from apps.api.orchestration.coordinator import Coordinator, drafts_to_tasks
from apps.api.orchestration.critique import render_critique, review
from apps.api.orchestration.graph_events import (
    edge_feedback,
    node_output,
    node_status_changed,
    traced_events_for_plan,
)
from apps.api.orchestration.graph_validator import GraphValidationError
from apps.api.orchestration.llm import (
    ProviderStatus,
    UnknownProvider,
    choose_model,
    configure,
    get_llm,
    provider_status,
)
from apps.api.orchestration.reasoning import ReasoningFailed
from apps.api.orchestration.reporting import report_on_run
from apps.api.orchestration.scheduler import Scheduler, ScheduleResult
from apps.api.orchestration.task_planner import PlannedTask, TaskStatus
from apps.api.trace_hub import TraceHub

logger = logging.getLogger(__name__)

NO_PROVIDER = (
    "I have no model to think with yet. Choose a provider and a model from the "
    "picker below the composer, and set this goal again."
)


def run_answer(result: Mapping[str, object]) -> str:
    """Renders a finished run as the reply the orchestrator sends back to chat.

    Args:
        result: The summary run_session returned for the finished run.

    Returns:
        answer: What the run produced, or why it stopped without producing it.
    """
    output = result.get("output")
    steps = [str(step) for step in output] if isinstance(output, list) else []
    if not steps:
        return "The run finished without producing any output."
    status = str(result.get("status", "completed"))
    if status != "completed":
        return f"Stopped as {status} after:\n" + "\n".join(steps)
    return "\n".join(steps)


async def datastore_unavailable(request: Request, error: Exception) -> JSONResponse:
    """Turns an unreachable datastore into a 503 the console can actually read.

    An unhandled database error is raised above the CORS layer, so the browser
    reports it as a CORS failure with no status code at all and the console has
    nothing to show the reviewer. Handling it here keeps the response inside the
    CORS middleware, which is the difference between "the API is down" and an
    error that looks like a misconfigured allowlist.

    Args:
        request: The request whose datastore call failed.
        error: The datastore error raised underneath the route.

    Returns:
        response: A 503 naming the datastore as the unavailable dependency.
    """
    logger.error("datastore unavailable for %s %s: %s", request.method, request.url.path, error)
    return JSONResponse(status_code=503, content={"detail": "datastore unavailable"})


def stopped_early(result: ScheduleResult, planned: Sequence[PlannedTask]) -> str:
    """Says which tasks a run did not get to, and why it did not get to them.

    Args:
        result: What the scheduler's pass over the graph produced.
        planned: The graph that pass was over.

    Returns:
        explanation: What is waiting on the reviewer, or what fell over.
    """
    titles = {task.id: task.title for task in planned}
    if result.waiting:
        held = ", ".join(titles.get(task_id, task_id) for task_id in result.waiting)
        return f"I have paused on work that needs your approval first: {held}."
    failed = ", ".join(titles.get(task_id, task_id) for task_id in result.failed)
    blocked = len(result.skipped)
    tail = f" {blocked} task(s) downstream never ran." if blocked else ""
    return f"I could not finish: {failed} failed.{tail}"


class ProviderRequest(BaseModel):
    """Carries the provider and credential the orchestrator should reason through.

    Attributes:
        provider: Which provider the credential belongs to.
        api_key: The credential, held in the API process and never returned.
    """

    provider: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    model: str = ""


class ModelRequest(BaseModel):
    """Carries the model a reviewer wants the team to reason through.

    Attributes:
        model: Model id, which must be one the configured credential can reach.
    """

    model: str = Field(min_length=1)


class TurnResult(BaseModel):
    """Represents what one turn of the conversation did with the run.

    Attributes:
        kind: Whether the coordinator answered, asked, planned, or was blocked.
        status: How the run ended, or why the turn produced no run at all.
        tasks: How many tasks the coordinator wove onto the canvas.
    """

    kind: str
    status: str
    tasks: int


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
    conversations = Conversations()
    if settings.otel_exporter_otlp_endpoint:
        setup_tracing(app, service_name=settings.otel_service_name)
    app.add_exception_handler(DatastoreUnavailable, datastore_unavailable)
    app.include_router(audit_router)
    app.include_router(approvals_router)
    app.add_route("/metrics", metrics_endpoint)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins(),
        allow_credentials=True,
        # PUT is what configures the model provider; without it the browser
        # preflight fails and the console cannot save a key at all.
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
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

    @app.get("/settings/provider")
    async def read_provider() -> ProviderStatus:
        """Reports which provider is configured, without revealing the key.

        Returns:
            status: The provider and model in use, and the choices on offer.
        """
        return provider_status()

    @app.put("/settings/model")
    async def write_model(body: ModelRequest) -> ProviderStatus:
        """Repins the team to another model the configured credential can reach.

        Args:
            body: The model the reviewer wants the team to reason through.

        Returns:
            status: The provider and model now in use.

        Raises:
            HTTPException: When nothing is configured, or the model is not on offer.
        """
        try:
            return await choose_model(body.model)
        except UnknownProvider as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except ReasoningFailed as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.put("/settings/provider")
    async def write_provider(body: ProviderRequest) -> ProviderStatus:
        """Points the orchestrator at a credential for the life of this process.

        The credential is verified against the provider before it is kept, so a
        mistyped key is refused here rather than at the first goal someone sets.

        Args:
            body: The provider and credential to reason through.

        Returns:
            status: The provider and model now in use.

        Raises:
            HTTPException: When the provider is unknown or the key is rejected.
        """
        try:
            return await configure(body.provider, body.api_key, body.model)
        except UnknownProvider as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except ReasoningFailed as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/runs/{run_id}")
    async def start_run(run_id: str, body: StartRunRequest) -> TurnResult:
        """Takes one turn of the conversation about a goal, and runs what it plans.

        The coordinator decides what this turn is: a question back to the
        reviewer, an answer about work already done, or a task graph. Only the
        third one weaves nodes onto the canvas and puts the team to work; the
        reviewer hears back once, when there is something to hear.

        Args:
            run_id: Run the caller wants the conversation and graph streamed under.
            body: What the reviewer just said.

        Returns:
            outcome: What this turn did, and how the run it started ended.
        """
        llm = get_llm()

        async def say(text: str) -> None:
            """Sends one coordinator turn to everyone watching this run.

            Args:
                text: What the coordinator is telling the reviewer.
            """
            await hub.broadcast(
                run_id,
                {
                    "kind": "orchestrator_message",
                    "role": "orchestrator",
                    "payload": {"text": text},
                },
            )

        if llm is None:
            await say(NO_PROVIDER)
            return TurnResult(kind="blocked", status="unconfigured", tasks=0)

        conversation = conversations.append(run_id, "user", body.task)
        try:
            reply = await Coordinator(llm).respond(conversation)
        except ReasoningFailed as error:
            logger.warning("coordinator failed on run %s: %s", run_id, error)
            await say(f"I could not reach the model: {error}")
            return TurnResult(kind="blocked", status="failed", tasks=0)

        conversations.append(run_id, "assistant", reply.message)
        await say(reply.message)
        if reply.kind != "plan" or not reply.tasks:
            return TurnResult(kind=reply.kind, status=reply.kind, tasks=0)

        planned = drafts_to_tasks(reply.tasks)
        try:
            frames = traced_events_for_plan(run_id, planned)
        except GraphValidationError as error:
            logger.warning("coordinator planned an invalid graph on %s: %s", run_id, error)
            await say(f"That plan did not hold together ({error}), so I have not started it.")
            return TurnResult(kind="plan", status="invalid", tasks=0)
        await hub.broadcast_batch(run_id, frames)

        async def announce(task_id: str, status: TaskStatus, output: str) -> None:
            """Streams one task's transition to the canvas as it happens.

            Args:
                task_id: Task whose status moved.
                status: Lifecycle state the task moved into.
                output: What the task produced, once it has finished.
            """
            await hub.broadcast_batch(run_id, [node_status_changed(task_id, status, output)])

        goal = conversation[0].text if conversation else body.task

        async def work(task: PlannedTask, upstream: Mapping[str, str]) -> str:
            """Runs one planned task through the agent it was assigned to.

            The agent's answer is streamed to the run's viewers as it is
            written, so opening a running node shows the work in progress. The
            model client calls back synchronously, so each fragment is handed to
            the event loop as its own task rather than awaited in place.

            Args:
                task: The task the scheduler dispatched.
                upstream: What every task this one waits on produced.

            Returns:
                output: What the agent produced for this task.
            """
            pending: set[asyncio.Task[None]] = set()

            def stream(delta: str) -> None:
                """Ships one fragment of this task's output to the canvas.

                Args:
                    delta: The text the agent has just produced.
                """
                shipped = asyncio.create_task(
                    hub.broadcast_batch(run_id, [node_output(task.id, delta)])
                )
                pending.add(shipped)
                shipped.add_done_callback(pending.discard)

            try:
                return await run_task(
                    llm, goal, task, upstream, stream, scheduler.note_for(task.id)
                )
            finally:
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)

        async def judge(
            task: PlannedTask, upstream: Mapping[str, str]
        ) -> tuple[str, bool, Mapping[str, str]]:
            """Has the critic judge the work its task depends on.

            Args:
                task: The critic's own task.
                upstream: What every task it reviews produced.

            Returns:
                verdict: The written review, whether it accepted, and one note
                    per task it wants changed.
            """
            critique = await review(llm, goal, task, upstream)
            notes = {note.task_id: note.problem for note in critique.notes}
            return render_critique(critique), critique.verdict == "accept", notes

        async def sent_back(critic: str, author: str, note: str) -> None:
            """Draws the path a critic sent one task's work back along.

            Args:
                critic: Task that rejected the work.
                author: Task being asked to do it again.
                note: What the critic asked the author to change.
            """
            await hub.broadcast_batch(run_id, [edge_feedback(critic, author, note)])

        scheduler = Scheduler(planned, work, announce, judge, sent_back)
        result = await scheduler.run()

        # Every run ends with something to read: the artifact the team produced
        # and the coordinator's own verdict on it. A run that stopped early has
        # no finished artifact, so it says what it is waiting on instead.
        if result.outputs:
            report = await report_on_run(llm, goal, result.outputs)
            for turn in (report.artifact, report.feedback):
                conversations.append(run_id, "assistant", turn)
                await say(turn)
        if result.status != "completed":
            held = stopped_early(result, planned)
            conversations.append(run_id, "assistant", held)
            await say(held)
        return TurnResult(kind="plan", status=result.status, tasks=len(planned))

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

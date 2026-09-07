#!/usr/bin/env python3
"""
test_run_routes.py --- integration tests for the run conversation route

Contains:
    StubLLM: a reasoning client that plans a fixed graph without a network
    stub_llm(): installs the stub as the live client for one test
    client(): builds a test client over the real application
    test_a_goal_is_planned_and_run(): verifies a goal weaves a graph and runs it
    test_a_question_plans_nothing(): verifies a clarifying turn starts no run
    test_a_running_task_streams_its_output(): verifies fragments reach the canvas
    test_a_finished_run_reports_an_artifact_and_feedback(): verifies the close
    test_a_run_without_a_provider_is_blocked(): verifies the unconfigured reply
    test_a_coordinator_failure_is_reported(): verifies a model outage is readable
    test_an_invalid_plan_never_starts(): verifies a cyclic plan is refused
    test_starting_a_run_rejects_an_empty_task(): verifies the request is validated
    test_a_finished_run_answers_with_its_output(): verifies the chat reply text
    test_a_bounded_run_says_why_it_stopped(): verifies a stopped run explains itself
    test_a_run_that_produced_nothing_still_answers(): verifies the empty reply
    test_a_paused_run_names_what_needs_approval(): verifies the approval message
    test_a_failed_run_names_what_fell_over(): verifies the failure message
    test_a_datastore_outage_answers_503(): verifies an outage is readable
    test_a_datastore_outage_keeps_its_cors_headers(): verifies the browser can read it
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from apps.api.main import create_app
from apps.api.orchestration import llm as registry
from apps.api.orchestration.coordinator import CoordinatorReply, TaskDraft
from apps.api.orchestration.critique import Critique
from apps.api.orchestration.reasoning import ChatMessage, OnDelta
from apps.api.orchestration.reporting import RunReport

PLAN = [
    TaskDraft(id="task-1", title="gather the sources", assignee="researcher", rationale="a"),
    TaskDraft(id="task-2", title="draft the summary", assignee="writer", rationale="b"),
    TaskDraft(
        id="task-3",
        title="check the citations",
        assignee="critic",
        depends_on=["task-2"],
        rationale="c",
    ),
]


class StubLLM:
    """Plans one fixed graph so the route can be exercised without a network.

    Attributes:
        name: Provider name the console would show.
        model: Model name the console would show.
        reply: What the coordinator turn returns.
    """

    name = "stub"
    model = "stub-1"

    def __init__(self, reply: CoordinatorReply | None = None) -> None:
        """Initializes the stub with the reply its coordinator turn returns.

        Args:
            reply: What respond() should come back with, defaulting to a plan.
        """
        self.reply = reply or CoordinatorReply(
            kind="plan", message="Planning three tasks.", tasks=PLAN
        )

    async def verify(self) -> None:
        """Accepts any credential, because there is nothing to check."""

    async def list_models(self) -> list[str]:
        """Returns the one model this stub pretends to offer.

        Returns:
            models: A single model id.
        """
        return [self.model]

    async def complete(
        self,
        system: str,
        prompt: str,
        on_delta: OnDelta | None = None,
    ) -> str:
        """Returns a deterministic answer, in fragments when asked to stream.

        Args:
            system: Standing instructions, ignored by the stub.
            prompt: The rendered prompt, ignored by the stub.
            on_delta: Called with each fragment, as a real provider would.

        Returns:
            answer: A fixed line standing in for the agent's work.
        """
        _ = (system, prompt)
        fragments = ["stub ", "output"]
        if on_delta is not None:
            for fragment in fragments:
                on_delta(fragment)
        return "".join(fragments)

    async def parse(
        self,
        system: str,
        messages: list[ChatMessage],
        schema: type[BaseModel],
    ) -> BaseModel:
        """Returns an answer in the shape the caller asked for.

        The stub honours the schema rather than always handing back a
        coordinator reply, because the run path asks it for three different
        shapes: the plan, a critic's verdict, and the closing report.

        Args:
            system: Standing instructions, ignored by the stub.
            messages: The conversation, ignored by the stub.
            schema: Shape the answer has to satisfy.

        Returns:
            answer: The fixed reply for that shape.
        """
        _ = (system, messages)
        if schema is RunReport:
            return RunReport(artifact="stub artifact", feedback="stub feedback")
        if schema is Critique:
            return Critique(verdict="accept", summary="stub review")
        return self.reply


@pytest.fixture
def stub_llm() -> Iterator[StubLLM]:
    """Installs a stub reasoning client as the live one for the duration of a test.

    Yields:
        stub: The stub the route will reason through.
    """
    stub = StubLLM()
    previous = registry._live
    registry._live = stub
    yield stub
    registry._live = previous


@pytest.fixture
def client() -> TestClient:
    """Builds a test client over the real application.

    Returns:
        client: Test client bound to a freshly built application.
    """
    return TestClient(create_app())


def test_a_goal_is_planned_and_run(client: TestClient, stub_llm: StubLLM) -> None:
    """Verifies one goal is decomposed into a graph and executed."""
    response = client.post("/runs/run-1", json={"task": "summarise the filings"})
    assert response.status_code == 200
    assert response.json() == {"kind": "plan", "status": "completed", "tasks": 3}


@pytest.mark.asyncio
async def test_a_running_task_streams_its_output() -> None:
    """Verifies an agent's answer reaches the canvas while it is still writing.

    A reviewer who opens a running node should read the work appearing, so the
    fragments have to be shipped as the model produces them rather than folded
    into the frame that says the task is done.
    """
    from apps.api.orchestration.agents import run_task
    from apps.api.orchestration.task_planner import PlannedTask

    seen: list[str] = []
    output = await run_task(
        StubLLM(),
        "a goal",
        PlannedTask(id="task-1", title="write it", assignee="writer"),
        {},
        seen.append,
    )
    assert seen == ["stub ", "output"]
    assert output == "stub output"


def test_a_question_plans_nothing(client: TestClient, stub_llm: StubLLM) -> None:
    """Verifies a turn the coordinator answers starts no run at all."""
    stub_llm.reply = CoordinatorReply(kind="question", message="Which filings?")
    response = client.post("/runs/run-2", json={"task": "summarise them"})
    assert response.json() == {"kind": "question", "status": "question", "tasks": 0}


@pytest.mark.asyncio
async def test_a_finished_run_reports_an_artifact_and_feedback() -> None:
    """Verifies a finished run hands back a deliverable and a verdict on it."""
    from apps.api.orchestration.reporting import report_on_run

    report = await report_on_run(StubLLM(), "a goal", {"task-1": "some work"})
    assert report.artifact == "stub artifact"
    assert report.feedback == "stub feedback"


@pytest.mark.asyncio
async def test_a_run_with_no_output_still_reports_something() -> None:
    """Verifies an empty run is reported rather than silently dropped."""
    from apps.api.orchestration.reporting import report_on_run

    report = await report_on_run(StubLLM(), "a goal", {})
    assert report.artifact != ""
    assert report.feedback != ""


def test_a_run_without_a_provider_is_blocked(client: TestClient) -> None:
    """Verifies a goal set with no model configured plans nothing."""
    previous = registry._live
    registry._live = None
    try:
        response = client.post("/runs/run-3", json={"task": "do the thing"})
    finally:
        registry._live = previous
    assert response.json() == {"kind": "blocked", "status": "unconfigured", "tasks": 0}


def test_a_coordinator_failure_is_reported(client: TestClient, stub_llm: StubLLM) -> None:
    """Verifies a model that cannot answer ends the turn readably."""
    from apps.api.orchestration.reasoning import ReasoningFailed

    async def fail(
        system: str,
        messages: list[ChatMessage],
        schema: type[BaseModel],
    ) -> BaseModel:
        """Raises as a provider outage would.

        Args:
            system: Standing instructions, ignored.
            messages: The conversation, ignored.
            schema: Shape the caller wanted, ignored.

        Raises:
            ReasoningFailed: Always.
        """
        _ = (system, messages, schema)
        raise ReasoningFailed("the model is down")

    stub_llm.parse = fail  # type: ignore[method-assign]
    response = client.post("/runs/run-4", json={"task": "do the thing"})
    assert response.json()["status"] == "failed"


def test_an_invalid_plan_never_starts(client: TestClient, stub_llm: StubLLM) -> None:
    """Verifies a plan with a cycle is refused before anything reaches the canvas."""
    stub_llm.reply = CoordinatorReply(
        kind="plan",
        message="Planning two tasks.",
        tasks=[
            TaskDraft(
                id="task-1",
                title="a",
                assignee="executor",
                depends_on=["task-2"],
                rationale="a",
            ),
            TaskDraft(
                id="task-2",
                title="b",
                assignee="executor",
                depends_on=["task-1"],
                rationale="b",
            ),
        ],
    )
    response = client.post("/runs/run-5", json={"task": "do the thing"})
    assert response.json() == {"kind": "plan", "status": "invalid", "tasks": 0}


def test_starting_a_run_rejects_an_empty_task(client: TestClient) -> None:
    """Verifies an empty instruction never reaches the coordinator."""
    assert client.post("/runs/run-6", json={"task": ""}).status_code == 422


def test_a_run_with_no_viewers_still_finishes(client: TestClient, stub_llm: StubLLM) -> None:
    """Verifies broadcasting to an empty room never blocks the run."""
    assert client.post("/runs/run-7", json={"task": "nobody watching"}).status_code == 200


def test_a_datastore_outage_answers_503(client: TestClient) -> None:
    """Verifies an unreachable datastore answers 503 rather than a bare 500."""
    response = client.get("/audit/run-unreachable")
    assert response.status_code == 503
    assert response.json()["detail"] == "datastore unavailable"


def test_a_datastore_outage_keeps_its_cors_headers(client: TestClient) -> None:
    """Verifies an outage response still carries the headers the console needs.

    An unhandled database error is raised above the CORS middleware, so the
    browser reports a CORS failure and the console never sees the status code.
    """
    response = client.get("/audit/run-unreachable", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 503
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_a_finished_run_answers_with_its_output() -> None:
    """Verifies the orchestrator's chat reply carries what the run produced."""
    from apps.api.main import run_answer

    answer = run_answer({"status": "completed", "output": ["done: a", "done: b"]})
    assert answer == "done: a\ndone: b"


def test_a_bounded_run_says_why_it_stopped() -> None:
    """Verifies a run that hit its bound explains itself rather than looking done."""
    from apps.api.main import run_answer

    answer = run_answer({"status": "revision-bounded", "output": ["done: a"]})
    assert answer.startswith("Stopped as revision-bounded")


def test_a_run_that_produced_nothing_still_answers() -> None:
    """Verifies an empty run replies rather than sending a blank chat turn."""
    from apps.api.main import run_answer

    assert run_answer({"status": "completed", "output": []}) != ""


def test_a_paused_run_names_what_needs_approval() -> None:
    """Verifies a run held for approval says which work is waiting."""
    from apps.api.main import stopped_early
    from apps.api.orchestration.scheduler import ScheduleResult
    from apps.api.orchestration.task_planner import PlannedTask

    result = ScheduleResult(status="awaiting-approval", waiting=("task-2",))
    planned = [PlannedTask(id="task-2", title="send the email")]
    assert "send the email" in stopped_early(result, planned)


def test_a_failed_run_names_what_fell_over() -> None:
    """Verifies a failed run names the task that failed and what it blocked."""
    from apps.api.main import stopped_early
    from apps.api.orchestration.scheduler import ScheduleResult
    from apps.api.orchestration.task_planner import PlannedTask

    result = ScheduleResult(status="failed", failed=("task-1",), skipped=("task-2",))
    planned = [PlannedTask(id="task-1", title="fetch the filings")]
    message = stopped_early(result, planned)
    assert "fetch the filings" in message
    assert "1 task(s) downstream" in message

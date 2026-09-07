#!/usr/bin/env python3
"""
test_scheduler.py --- unit tests for the deterministic wave scheduler

Contains:
    record(): builds a status sink that appends every transition to a list
    always(): builds a task runner that returns a fixed output
    test_a_chain_runs_in_dependency_order(): verifies edges are respected
    test_independent_tasks_share_one_wave(): verifies parallel dispatch
    test_a_wave_is_dispatched_in_a_stable_order(): verifies replayable ordering
    test_a_failed_task_blocks_only_its_dependents(): verifies failure containment
    test_a_task_needing_approval_is_never_run(): verifies the approval pause
    test_approval_holds_back_the_work_behind_it(): verifies dependents wait too
    test_every_task_reports_running_then_done(): verifies the status stream
    test_an_upstream_result_reaches_its_dependent(): verifies output threading
    test_an_empty_graph_completes(): verifies the degenerate case
    test_a_rejected_task_runs_again(): verifies the critic's revision loop
    test_a_critic_that_accepts_never_revises(): verifies acceptance ends it
    test_a_critic_runs_out_of_revisions(): verifies the loop is bounded
    test_a_rejection_is_announced(): verifies the feedback path is reported
"""

import pytest

from apps.api.orchestration.scheduler import (
    Reviewer,
    Scheduler,
    StatusSink,
    TaskRunner,
)
from apps.api.orchestration.task_planner import PlannedTask, TaskStatus


def record(seen: list[tuple[str, TaskStatus]]) -> StatusSink:
    """Builds a status sink that appends every transition to a list.

    Args:
        seen: List the sink appends to.

    Returns:
        sink: The status sink to hand the scheduler.
    """

    async def sink(task_id: str, status: TaskStatus, output: str) -> None:
        """Appends one transition.

        Args:
            task_id: Task whose status moved.
            status: Lifecycle state it moved into.
            output: What the task produced, ignored by this sink.
        """
        _ = output
        seen.append((task_id, status))

    return sink


def always(output: str = "ok", order: list[str] | None = None) -> TaskRunner:
    """Builds a task runner that returns a fixed output for every task.

    Args:
        output: What every task produces.
        order: Optional list the runner records dispatch order in.

    Returns:
        runner: The task runner to hand the scheduler.
    """

    async def runner(task: PlannedTask, upstream: dict[str, str]) -> str:
        """Returns the fixed output.

        Args:
            task: The task being run.
            upstream: What its dependencies produced.

        Returns:
            output: The fixed output this runner was built with.
        """
        _ = upstream
        if order is not None:
            order.append(task.id)
        return output

    return runner


CHAIN = (
    PlannedTask(id="task-1", title="a"),
    PlannedTask(id="task-2", title="b", depends_on=("task-1",)),
)
FAN = (
    PlannedTask(id="task-1", title="a"),
    PlannedTask(id="task-2", title="b"),
    PlannedTask(id="task-3", title="c"),
)


@pytest.mark.asyncio
async def test_a_chain_runs_in_dependency_order() -> None:
    """Verifies a task never starts before the task it waits on has finished."""
    order: list[str] = []
    result = await Scheduler(CHAIN, always(order=order), record([])).run()
    assert order == ["task-1", "task-2"]
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_independent_tasks_share_one_wave() -> None:
    """Verifies tasks that wait on nothing all finish in a single pass."""
    result = await Scheduler(FAN, always(), record([])).run()
    assert result.completed == ("task-1", "task-2", "task-3")


@pytest.mark.asyncio
async def test_a_wave_is_dispatched_in_a_stable_order() -> None:
    """Verifies the same graph dispatches in the same order every time.

    A replayed trace is only comparable to the run it came from if the waves
    went out in the same sequence, so the order is by id rather than by chance.
    """
    shuffled = tuple(reversed(FAN))
    order: list[str] = []
    await Scheduler(shuffled, always(order=order), record([])).run()
    assert order == ["task-1", "task-2", "task-3"]


@pytest.mark.asyncio
async def test_a_failed_task_blocks_only_its_dependents() -> None:
    """Verifies one agent failing leaves the independent work alone."""
    tasks = (
        PlannedTask(id="task-1", title="a"),
        PlannedTask(id="task-2", title="b", depends_on=("task-1",)),
        PlannedTask(id="task-3", title="c"),
    )

    async def runner(task: PlannedTask, upstream: dict[str, str]) -> str:
        """Fails the first task and returns for every other one.

        Args:
            task: The task being run.
            upstream: What its dependencies produced.

        Returns:
            output: A fixed output for the tasks that do not fail.

        Raises:
            RuntimeError: When the first task is dispatched.
        """
        _ = upstream
        if task.id == "task-1":
            raise RuntimeError("the agent fell over")
        return "ok"

    result = await Scheduler(tasks, runner, record([])).run()
    assert result.failed == ("task-1",)
    assert result.completed == ("task-3",)
    assert result.skipped == ("task-2",)
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_a_task_needing_approval_is_never_run() -> None:
    """Verifies work a human has to sign off on is held, not executed."""
    tasks = (PlannedTask(id="task-1", title="send it", status="awaiting-approval"),)
    order: list[str] = []
    result = await Scheduler(tasks, always(order=order), record([])).run()
    assert order == []
    assert result.waiting == ("task-1",)
    assert result.status == "awaiting-approval"


@pytest.mark.asyncio
async def test_approval_holds_back_the_work_behind_it() -> None:
    """Verifies a task waiting on held work never starts either."""
    tasks = (
        PlannedTask(id="task-1", title="send it", status="awaiting-approval"),
        PlannedTask(id="task-2", title="report", depends_on=("task-1",)),
    )
    result = await Scheduler(tasks, always(), record([])).run()
    assert result.skipped == ("task-2",)


@pytest.mark.asyncio
async def test_every_task_reports_running_then_done() -> None:
    """Verifies the canvas is told about both ends of a task, in order."""
    seen: list[tuple[str, TaskStatus]] = []
    await Scheduler(CHAIN, always(), record(seen)).run()
    assert seen == [
        ("task-1", "running"),
        ("task-1", "done"),
        ("task-2", "running"),
        ("task-2", "done"),
    ]


@pytest.mark.asyncio
async def test_an_upstream_result_reaches_its_dependent() -> None:
    """Verifies a task is handed what the tasks it waits on produced."""
    handed: list[dict[str, str]] = []

    async def runner(task: PlannedTask, upstream: dict[str, str]) -> str:
        """Records what it was handed and returns its own id.

        Args:
            task: The task being run.
            upstream: What its dependencies produced.

        Returns:
            output: The task's own id, so the dependent sees something specific.
        """
        handed.append(dict(upstream))
        return f"{task.id} output"

    await Scheduler(CHAIN, runner, record([])).run()
    assert handed[1] == {"task-1": "task-1 output"}


@pytest.mark.asyncio
async def test_an_empty_graph_completes() -> None:
    """Verifies a graph with no tasks settles rather than spinning."""
    result = await Scheduler((), always(), record([])).run()
    assert result.status == "completed"
    assert result.completed == ()


REVIEWED = (
    PlannedTask(id="task-1", title="draft it", assignee="writer"),
    PlannedTask(id="task-2", title="review it", assignee="critic", depends_on=("task-1",)),
)


def verdicts(accepts_on: int) -> tuple[Reviewer, dict[str, int]]:
    """Builds a reviewer that rejects until the given attempt, then accepts.

    Args:
        accepts_on: Which attempt accepts, counting from one.

    Returns:
        reviewer: The reviewer to hand the scheduler, and its attempt counter.
    """
    attempts = {"count": 0}

    async def reviewer(
        task: PlannedTask, upstream: dict[str, str]
    ) -> tuple[str, bool, dict[str, str]]:
        """Accepts on the configured attempt and rejects before it.

        Args:
            task: The critic's own task.
            upstream: What it reviews, ignored by the stub.

        Returns:
            verdict: The written review, whether it accepted, and its notes.
        """
        _ = (task, upstream)
        attempts["count"] += 1
        if attempts["count"] >= accepts_on:
            return "accepted", True, {}
        return "sent back", False, {"task-1": "add the numbers"}

    return reviewer, attempts


@pytest.mark.asyncio
async def test_a_rejected_task_runs_again() -> None:
    """Verifies a rejected author runs again and the critic re-reviews it."""
    order: list[str] = []
    reviewer, _ = verdicts(accepts_on=2)
    result = await Scheduler(REVIEWED, always(order=order), record([]), reviewer).run()
    assert order == ["task-1", "task-1"]
    assert result.revisions == {"task-2": 1}
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_a_critic_that_accepts_never_revises() -> None:
    """Verifies work the critic accepts is not sent back at all."""
    order: list[str] = []
    reviewer, _ = verdicts(accepts_on=1)
    result = await Scheduler(REVIEWED, always(order=order), record([]), reviewer).run()
    assert order == ["task-1"]
    assert result.revisions == {}


@pytest.mark.asyncio
async def test_a_critic_runs_out_of_revisions() -> None:
    """Verifies a critic that never accepts stops rather than looping forever."""
    reviewer, attempts = verdicts(accepts_on=99)
    result = await Scheduler(REVIEWED, always(), record([]), reviewer, max_revisions=2).run()
    assert result.revisions == {"task-2": 2}
    assert result.bounded == ("task-2",)
    assert result.status == "revision-bounded"
    assert attempts["count"] == 3


@pytest.mark.asyncio
async def test_a_rejection_is_announced() -> None:
    """Verifies the canvas is told which task was sent back, and why."""
    seen: list[tuple[str, str, str]] = []

    async def on_feedback(critic: str, author: str, note: str) -> None:
        """Records one rejection.

        Args:
            critic: Task that rejected the work.
            author: Task asked to do it again.
            note: What the critic wants changed.
        """
        seen.append((critic, author, note))

    reviewer, _ = verdicts(accepts_on=2)
    await Scheduler(REVIEWED, always(), record([]), reviewer, on_feedback).run()
    assert seen == [("task-2", "task-1", "add the numbers")]

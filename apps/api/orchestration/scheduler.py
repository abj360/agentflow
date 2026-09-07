#!/usr/bin/env python3
"""
scheduler.py --- runs a planned task graph across the team, wave by wave

Contains:
    TaskRunner: what the scheduler calls to do one task's work
    StatusSink: what the scheduler reports every status transition to
    ScheduleResult: what one pass over the task graph produced
    ready_tasks(): the tasks whose dependencies have all finished
    Scheduler: executes a validated task graph deterministically
    Scheduler.run(): runs until the graph finishes, fails, or waits on a human
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

from apps.api.orchestration.task_planner import PlannedTask, TaskStatus

TaskRunner = Callable[[PlannedTask, Mapping[str, str]], Awaitable[str]]
StatusSink = Callable[[str, TaskStatus, str], Awaitable[None]]

RunStatus = Literal["completed", "failed", "awaiting-approval", "stalled"]


@dataclass(frozen=True)
class ScheduleResult:
    """Represents what one pass over the task graph produced.

    Attributes:
        status: How the pass ended for the graph as a whole.
        outputs: What each finished task produced, keyed by task id.
        completed: Ids of the tasks that finished, in the order they settled.
        failed: Ids of the tasks that raised, in the order they settled.
        waiting: Ids of the tasks held back for a human to approve.
        skipped: Ids of the tasks that never became runnable.
    """

    status: RunStatus
    outputs: Mapping[str, str] = field(default_factory=dict)
    completed: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    waiting: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()


def ready_tasks(
    tasks: Sequence[PlannedTask],
    done: frozenset[str],
    settled: frozenset[str],
) -> list[PlannedTask]:
    """Returns the tasks whose dependencies have all finished.

    Sorted by id rather than left in plan order: two runs of the same graph then
    dispatch the same waves in the same sequence, which is what makes a replay
    of the trace comparable to the run it came from.

    Args:
        tasks: Every task in the graph.
        done: Ids of the tasks that have finished successfully.
        settled: Ids of the tasks that will not be dispatched again.

    Returns:
        ready: The tasks that can start now, in a stable order.
    """
    return sorted(
        (
            task
            for task in tasks
            if task.id not in settled and all(need in done for need in task.depends_on)
        ),
        key=lambda task: task.id,
    )


class Scheduler:
    """Executes a validated task graph across the team, one wave at a time.

    A wave is every task whose dependencies are already satisfied. The tasks in
    a wave run concurrently because nothing in the graph says they must not; the
    waves themselves are ordered, which is the whole point of the dependencies.

    Attributes:
        tasks: The planned graph this scheduler is running.
        run_task: What the scheduler calls to do one task's work.
        on_status: What the scheduler reports every status transition to.
    """

    def __init__(
        self,
        tasks: Sequence[PlannedTask],
        run_task: TaskRunner,
        on_status: StatusSink,
    ) -> None:
        """Initializes the scheduler against one planned graph.

        Args:
            tasks: The validated task graph to run.
            run_task: Called to do one task's work and return its output.
            on_status: Called with every status transition and, once a task
                finishes, whatever it produced.
        """
        self.tasks = tuple(tasks)
        self.run_task = run_task
        self.on_status = on_status

    async def run(self) -> ScheduleResult:
        """Runs the graph until it finishes, fails, or waits on a human.

        Returns:
            result: What the pass produced, and which tasks are in which state.
        """
        outputs: dict[str, str] = {}
        done: set[str] = set()
        settled: set[str] = set()
        completed: list[str] = []
        failed: list[str] = []
        waiting: list[str] = []

        while True:
            ready = ready_tasks(self.tasks, frozenset(done), frozenset(settled))
            held = [task for task in ready if task.status == "awaiting-approval"]
            for task in held:
                settled.add(task.id)
                waiting.append(task.id)
                await self.on_status(task.id, "awaiting-approval", "")

            runnable = [task for task in ready if task.status != "awaiting-approval"]
            if not runnable:
                break

            for task in runnable:
                settled.add(task.id)
                await self.on_status(task.id, "running", "")

            results = await asyncio.gather(
                *(self._settle(task, outputs) for task in runnable),
                return_exceptions=False,
            )
            for task, output in zip(runnable, results, strict=True):
                if output is None:
                    failed.append(task.id)
                    await self.on_status(task.id, "failed", "")
                    continue
                outputs[task.id] = output
                done.add(task.id)
                completed.append(task.id)
                await self.on_status(task.id, "done", output)

        skipped = tuple(task.id for task in self.tasks if task.id not in settled)
        return ScheduleResult(
            status=self._status(failed, waiting, skipped),
            outputs=outputs,
            completed=tuple(completed),
            failed=tuple(failed),
            waiting=tuple(waiting),
            skipped=skipped,
        )

    async def _settle(self, task: PlannedTask, outputs: Mapping[str, str]) -> str | None:
        """Runs one task and reports failure as a value rather than an exception.

        One agent failing is a state the graph has a node for, not a reason to
        abandon the tasks running beside it in the same wave.

        Args:
            task: The task to run.
            outputs: What every finished task has produced so far.

        Returns:
            output: What the task produced, or None when it failed.
        """
        try:
            return await self.run_task(task, outputs)
        except Exception:  # an agent may fail any number of ways; the node says so
            return None

    @staticmethod
    def _status(
        failed: Sequence[str],
        waiting: Sequence[str],
        skipped: Sequence[str],
    ) -> RunStatus:
        """Reduces the per-task outcomes to one status for the whole pass.

        Args:
            failed: Ids of the tasks that raised.
            waiting: Ids of the tasks held for approval.
            skipped: Ids of the tasks that never became runnable.

        Returns:
            status: How the pass ended for the graph as a whole.
        """
        if failed:
            return "failed"
        if waiting:
            return "awaiting-approval"
        if skipped:
            return "stalled"
        return "completed"

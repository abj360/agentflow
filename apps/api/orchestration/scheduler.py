#!/usr/bin/env python3
"""
scheduler.py --- runs a planned task graph across the team, wave by wave

Contains:
    MAX_REVISIONS: how many times one critic may send its inputs back
    TaskRunner: what the scheduler calls to do one task's work
    Reviewer: what the scheduler calls to have a critic judge its inputs
    StatusSink: what the scheduler reports every status transition to
    OutputSink: what the scheduler reports each fragment of output to
    FeedbackSink: what the scheduler reports a critic's rejection to
    ScheduleResult: what one pass over the task graph produced
    ready_tasks(): the tasks whose dependencies have all finished
    Scheduler: executes a validated task graph deterministically
    Scheduler.run(): runs until the graph settles, fails, or waits on a human
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

from apps.api.orchestration.task_planner import PlannedTask, TaskStatus

logger = logging.getLogger(__name__)

# A critic that can send work back forever is a critic that never ships. Three
# passes is the same bound ADR-001 set on the fixed loop, applied per critic.
MAX_REVISIONS = 3

OutputSink = Callable[[str, str], Awaitable[None]]
TaskRunner = Callable[[PlannedTask, Mapping[str, str]], Awaitable[str]]
Reviewer = Callable[
    [PlannedTask, Mapping[str, str]], Awaitable[tuple[str, bool, Mapping[str, str]]]
]
FeedbackSink = Callable[[str, str, str], Awaitable[None]]

StatusSink = Callable[[str, TaskStatus, str], Awaitable[None]]

RunStatus = Literal[
    "completed",
    "failed",
    "awaiting-approval",
    "stalled",
    "revision-bounded",
]


@dataclass(frozen=True)
class ScheduleResult:
    """Represents what one pass over the task graph produced.

    Attributes:
        status: How the pass ended for the graph as a whole.
        outputs: What each finished task produced, keyed by task id.
        completed: Ids of the tasks that finished, in the order they settled.
        failed: Ids of the tasks that raised, in the order they settled.
        errors: Why each failed task failed, keyed by task id.
        waiting: Ids of the tasks held back for a human to approve.
        skipped: Ids of the tasks that never became runnable.
        revisions: How many times each critic sent its inputs back.
        bounded: Ids of the critics that ran out of revisions.
    """

    status: RunStatus
    outputs: Mapping[str, str] = field(default_factory=dict)
    completed: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    errors: Mapping[str, str] = field(default_factory=dict)
    waiting: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    revisions: Mapping[str, int] = field(default_factory=dict)
    bounded: tuple[str, ...] = ()


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
        review: Reviewer | None = None,
        on_feedback: FeedbackSink | None = None,
        max_revisions: int = MAX_REVISIONS,
    ) -> None:
        """Initializes the scheduler against one planned graph.

        Args:
            tasks: The validated task graph to run.
            run_task: Called to do one task's work and return its output.
            on_status: Called with every status transition and, once a task
                finishes, whatever it produced.
            review: Called instead of run_task for a critic's task, returning
                its written review, whether it accepted, and a note per task it
                wants changed. Without it a critic is run like any other agent
                and never sends anything back.
            on_feedback: Called with the critic, the task it is sending back,
                and why, so the canvas can draw the return path.
            max_revisions: How many times one critic may send its inputs back.
        """
        self.tasks = tuple(tasks)
        self.run_task = run_task
        self.on_status = on_status
        self.review = review
        self.on_feedback = on_feedback
        self.max_revisions = max_revisions
        self._notes: dict[str, str] = {}

    async def run(self) -> ScheduleResult:
        """Runs the graph until it settles, fails, or waits on a human.

        A critic that rejects its inputs unsettles them: the authors run again
        with the note attached, and the critic runs again after them. That
        repeats until the critic accepts or runs out of revisions, which is why
        this is a loop over waves rather than one pass through the graph.

        Returns:
            result: What the pass produced, and which tasks are in which state.
        """
        outputs: dict[str, str] = {}
        done: set[str] = set()
        settled: set[str] = set()
        completed: list[str] = []
        failed: list[str] = []
        errors: dict[str, str] = {}
        waiting: list[str] = []
        revisions: dict[str, int] = {}
        bounded: list[str] = []
        self._notes.clear()

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
            for task, outcome in zip(runnable, results, strict=True):
                output, failure, sent_back = outcome
                if output is None:
                    failed.append(task.id)
                    errors[task.id] = failure
                    # The reason travels with the frame, so a red node can be
                    # opened and read rather than only counted.
                    await self.on_status(task.id, "failed", failure)
                    continue

                outputs[task.id] = output
                done.add(task.id)
                completed.append(task.id)
                await self.on_status(task.id, "done", output)

                if not sent_back:
                    continue
                if revisions.get(task.id, 0) >= self.max_revisions:
                    # Out of passes. The work stands as it is, and the run says
                    # so rather than looping until someone kills it.
                    bounded.append(task.id)
                    continue
                revisions[task.id] = revisions.get(task.id, 0) + 1
                for author, note in sent_back.items():
                    if author not in done:
                        continue
                    self._notes[author] = note
                    outputs.pop(author, None)
                    done.discard(author)
                    settled.discard(author)
                    if author in completed:
                        completed.remove(author)
                    if self.on_feedback is not None:
                        await self.on_feedback(task.id, author, note)
                    await self.on_status(author, "pending", "")
                # The critic runs again once its authors have.
                done.discard(task.id)
                settled.discard(task.id)
                if task.id in completed:
                    completed.remove(task.id)

        skipped = tuple(task.id for task in self.tasks if task.id not in settled)
        status = self._status(failed, waiting, skipped)
        return ScheduleResult(
            status="revision-bounded" if bounded and status == "completed" else status,
            outputs=outputs,
            errors=errors,
            completed=tuple(completed),
            failed=tuple(failed),
            waiting=tuple(waiting),
            skipped=skipped,
            revisions=revisions,
            bounded=tuple(bounded),
        )

    async def _settle(
        self, task: PlannedTask, outputs: Mapping[str, str]
    ) -> tuple[str | None, str, Mapping[str, str]]:
        """Runs one task and reports failure as a value rather than an exception.

        One agent failing is a state the graph has a node for, not a reason to
        abandon the tasks running beside it in the same wave.

        Args:
            task: The task to run.
            outputs: What every finished task has produced so far.

        Returns:
            outcome: What the task produced, the reason it failed, and the notes
                it is sending back to its authors when it is a critic that
                rejected their work.
        """
        try:
            if self.review is not None and task.assignee == "critic":
                written, accepted, notes = await self.review(task, outputs)
                return written, "", {} if accepted else notes
            return await self.run_task(task, outputs), "", {}
        except Exception as error:  # an agent may fail any number of ways
            # The node turns red either way, but a red node with no reason on it
            # is not something anyone can act on.
            logger.exception("task %s (%s) failed", task.id, task.assignee)
            return None, f"{type(error).__name__}: {error}", {}

    def note_for(self, task_id: str) -> str:
        """Returns the critic's note a task has to act on, if it has one.

        Args:
            task_id: The task about to run.

        Returns:
            note: What the critic asked this task to change, or an empty string.
        """
        return self._notes.get(task_id, "")

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

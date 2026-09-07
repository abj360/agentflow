#!/usr/bin/env python3
"""
critique.py --- what a critic decides about the work it was given to review

Contains:
    CRITIC_SYSTEM: standing instructions a review is written under
    TaskNote: one thing a critic wants one task to fix
    Critique: a critic's verdict, and what it wants changed
    render_critique(): renders a verdict as the text the node shows
    review(): asks the critic to judge the work its task depends on
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, Field

from apps.api.orchestration.reasoning import ChatMessage, ReasoningClient
from apps.api.orchestration.task_planner import PlannedTask

CRITIC_SYSTEM = """You are the critic on a small agent team. You review the work you are
given against the goal, and you decide one of two things:

- "accept" - the work answers the goal. Say briefly why it holds up.
- "revise" - it does not, and you say exactly what each author must change.

When you revise, every note names the task it is addressed to and states the
problem as a specific, actionable change: what is missing, what is unsupported,
what contradicts something else, what the goal asked for and did not get. Never
write a note that only says the work could be better, and never ask for a change
you cannot justify from the goal.

Accept when the work is sound. Sending competent work back for another pass
costs the team a cycle and gains nothing; inventing objections to look rigorous
is worse than accepting.
"""


class TaskNote(BaseModel):
    """Represents one thing a critic wants one task to fix.

    Attributes:
        task_id: The task the note is addressed to.
        problem: The specific change that task has to make.
    """

    task_id: str
    problem: str


class Critique(BaseModel):
    """Represents a critic's verdict, and what it wants changed.

    Attributes:
        verdict: Whether the work is accepted or has to be revised.
        summary: The critic's reasoning, in a few sentences.
        notes: One note per task that has to change, empty on acceptance.
    """

    verdict: Literal["accept", "revise"]
    summary: str
    notes: list[TaskNote] = Field(default_factory=list)


def render_critique(critique: Critique) -> str:
    """Renders a verdict as the text the critic's node shows.

    Args:
        critique: The verdict to render.

    Returns:
        rendered: The summary, and the notes when it asked for changes.
    """
    if critique.verdict == "accept":
        return f"**Accepted.** {critique.summary}"
    notes = "\n".join(f"- `{note.task_id}`: {note.problem}" for note in critique.notes)
    return f"**Sent back for revision.** {critique.summary}\n\n{notes}"


async def review(
    llm: ReasoningClient,
    goal: str,
    task: PlannedTask,
    upstream: Mapping[str, str],
) -> Critique:
    """Asks the critic to judge the work its task depends on.

    Args:
        llm: Model client the critic reasons through.
        goal: What the reviewer asked the team for.
        task: The critic's own task, naming what it reviews.
        upstream: Output of every task this review depends on, keyed by task id.

    Returns:
        critique: The verdict, and the notes the authors have to act on.

    Raises:
        ReasoningFailed: When the model returned nothing usable.
    """
    reviewed = "\n\n".join(
        f"### {task_id}\n{upstream.get(task_id, '(produced nothing)')}"
        for task_id in task.depends_on
    )
    messages: list[ChatMessage] = [
        {
            "role": "user",
            "content": (
                f"Overall goal: {goal}\n\n"
                f"Your review task: {task.title}\n\n"
                f"The work to review:\n\n{reviewed or '(nothing to review)'}"
            ),
        }
    ]
    return await llm.parse(CRITIC_SYSTEM, messages, Critique)

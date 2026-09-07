#!/usr/bin/env python3
"""
agents.py --- the team the coordinator hands each planned task to

Contains:
    AGENT_SYSTEM: the standing instructions each agent works under
    MAX_UPSTREAM_CHARS: how much of an upstream result one task is handed
    CLOSING_SYSTEM: how the team's work is turned into the reviewer's answer
    render_brief(): renders the goal, the task, and its upstream results
    run_task(): reasons one planned task through the model and returns its output
    summarise(): turns everything the team produced into one closing answer
"""

from __future__ import annotations

from collections.abc import Mapping

from apps.api.orchestration.reasoning import ReasoningClient
from apps.api.orchestration.task_planner import PlannedTask

MAX_UPSTREAM_CHARS = 4000

AGENT_SYSTEM: Mapping[str, str] = {
    "researcher": (
        "You are the researcher on a small agent team. You gather and organise "
        "what is known about one narrow question. Answer with findings, not with "
        "a plan and not with an offer to help. Say plainly when you are working "
        "from general knowledge rather than a source you actually read."
    ),
    "executor": (
        "You are the executor on a small agent team. You carry out one concrete "
        "step and report what it produced. You have no tools in this run, so "
        "produce the work itself in your answer and state any assumption the "
        "step rests on. No preamble."
    ),
    "writer": (
        "You are the writer on a small agent team. You turn the team's material "
        "into the finished text the goal asked for. Write the deliverable "
        "itself, not a description of it."
    ),
    "critic": (
        "You are the critic on a small agent team. You review the work against "
        "the goal and say what is wrong with it. Be specific and short: what is "
        "missing, what is unsupported, what should change. If it is sound, say "
        "so in one line rather than inventing objections."
    ),
}

DEFAULT_SYSTEM = AGENT_SYSTEM["executor"]

CLOSING_SYSTEM = (
    "You are reporting back to the person who set the goal. You are given what "
    "each agent on the team produced. Give them the finished result, in full, "
    "in the form the goal asked for. Do not narrate the process, do not list "
    "the tasks, and do not congratulate anyone."
)


def render_brief(
    goal: str,
    task: PlannedTask,
    upstream: Mapping[str, str],
) -> str:
    """Renders the goal, the task, and whatever upstream tasks produced.

    Each upstream result is truncated rather than dropped: a task that waits on
    four others should still see something from all four, and the alternative is
    one long result crowding the rest out of the context window.

    Args:
        goal: What the reviewer asked the team for.
        task: The task this agent is about to run.
        upstream: Output of every task this one depends on, keyed by task id.

    Returns:
        brief: The prompt handed to the agent.
    """
    parts = [f"Overall goal: {goal}", f"Your task: {task.title}"]
    for task_id in task.depends_on:
        result = upstream.get(task_id, "")
        if result:
            parts.append(f"Result of {task_id}:\n{result[:MAX_UPSTREAM_CHARS]}")
    parts.append("Do your task now and answer with its output only.")
    return "\n\n".join(parts)


async def run_task(
    llm: ReasoningClient,
    goal: str,
    task: PlannedTask,
    upstream: Mapping[str, str],
) -> str:
    """Reasons one planned task through the model and returns what it produced.

    Args:
        llm: Model client the agent reasons through.
        goal: What the reviewer asked the team for.
        task: The task to run.
        upstream: Output of every task this one depends on, keyed by task id.

    Returns:
        output: What the agent produced for this task.

    Raises:
        ReasoningFailed: When the model could not answer at all.
    """
    system = AGENT_SYSTEM.get(task.assignee, DEFAULT_SYSTEM)
    return await llm.complete(system, render_brief(goal, task, upstream))


async def summarise(llm: ReasoningClient, goal: str, outputs: Mapping[str, str]) -> str:
    """Turns everything the team produced into the one answer the reviewer reads.

    Args:
        llm: Model client the closing answer is written through.
        goal: What the reviewer asked the team for.
        outputs: What each finished task produced, keyed by task id.

    Returns:
        answer: The finished result, or the raw outputs when it cannot be written.
    """
    joined = "\n\n".join(f"{task_id}:\n{text}" for task_id, text in outputs.items())
    if not joined:
        return "The team produced nothing for this goal."
    try:
        return await llm.complete(
            CLOSING_SYSTEM, f"Goal: {goal}\n\nWhat the team produced:\n\n{joined}"
        )
    except Exception:  # the work is done either way; a failed write-up must not hide it
        return joined

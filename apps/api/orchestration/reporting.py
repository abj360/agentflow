#!/usr/bin/env python3
"""
reporting.py --- what the coordinator hands back when the team is done

Contains:
    REPORT_SYSTEM: standing instructions the closing report is written under
    RunReport: the artifact the run produced and the coordinator's verdict on it
    render_outputs(): renders what each task produced, for the report prompt
    report_on_run(): writes the artifact and the feedback for a finished run
    fallback_report(): the report used when the model cannot write one
"""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, Field

from apps.api.orchestration.reasoning import ChatMessage, ReasoningClient

REPORT_SYSTEM = """You are the coordinator, reporting back on work your team has finished.

You always return two things:

1. "artifact" - the deliverable itself, in full, in the form the goal asked
   for, written in markdown. This is the thing the person wanted: the brief,
   the comparison, the summary, the draft. Assemble it from what the agents
   produced. Do not describe it, do not summarise it, and do not tell the
   person what you are about to give them. If the agents produced material that
   does not belong in the deliverable, leave it out.
2. "feedback" - your own short assessment of the work, two to four sentences.
   Say how far it actually answers the goal, name anything thin, unsupported or
   missing, and say what you would do next if asked. Be candid: a report that
   claims everything is fine is worth nothing to the person reading it.

Never claim a source you were not given. If the team worked from general
knowledge rather than material it actually read, say so in the feedback.
"""


class RunReport(BaseModel):
    """Represents the artifact a run produced and the coordinator's verdict.

    Attributes:
        artifact: The deliverable itself, in markdown.
        feedback: The coordinator's candid assessment of the work.
    """

    artifact: str = Field(min_length=1)
    feedback: str = Field(min_length=1)


def render_outputs(outputs: Mapping[str, str]) -> str:
    """Renders what each task produced, in the shape the report is written from.

    Args:
        outputs: What each finished task produced, keyed by task id.

    Returns:
        rendered: One labelled block per task, oldest first.
    """
    return "\n\n".join(f"### {task_id}\n{text}" for task_id, text in outputs.items())


def fallback_report(outputs: Mapping[str, str]) -> RunReport:
    """Builds the report used when the model cannot write one.

    The team's work is finished either way, so a failed write-up must not be
    what hides it: the raw outputs are handed over instead, labelled as such.

    Args:
        outputs: What each finished task produced, keyed by task id.

    Returns:
        report: The raw outputs, and feedback saying the write-up failed.
    """
    rendered = render_outputs(outputs)
    return RunReport(
        artifact=rendered or "The team produced nothing for this goal.",
        feedback=(
            "I could not reach the model to write this up, so this is the raw "
            "output of each task rather than an assembled deliverable."
        ),
    )


async def report_on_run(
    llm: ReasoningClient,
    goal: str,
    outputs: Mapping[str, str],
) -> RunReport:
    """Writes the artifact and the feedback for a finished run.

    Args:
        llm: Model client the report is written through.
        goal: What the reviewer asked the team for.
        outputs: What each finished task produced, keyed by task id.

    Returns:
        report: The deliverable, and the coordinator's assessment of it.
    """
    if not outputs:
        return fallback_report(outputs)
    messages: list[ChatMessage] = [
        {
            "role": "user",
            "content": f"Goal: {goal}\n\nWhat the team produced:\n\n{render_outputs(outputs)}",
        }
    ]
    try:
        return await llm.parse(REPORT_SYSTEM, messages, RunReport)
    except Exception:  # a failed write-up must not swallow the work itself
        return fallback_report(outputs)

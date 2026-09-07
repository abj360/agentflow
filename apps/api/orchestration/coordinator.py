#!/usr/bin/env python3
"""
coordinator.py --- turns a conversation about a goal into a task graph

Contains:
    AGENTS: roles the coordinator may assign a task to
    COORDINATOR_SYSTEM: standing instructions the coordinator reasons under
    TaskDraft: one task the coordinator wants the team to run
    CoordinatorReply: what the coordinator decided to do with the latest turn
    Turn: one message in the conversation about a goal
    Coordinator: decides whether to answer, ask, or plan, and drafts the graph
    Coordinator.respond(): reasons about the conversation and returns a reply
    drafts_to_tasks(): turns the coordinator's drafts into planned tasks
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from apps.api.orchestration.reasoning import (
    ChatMessage,
    ReasoningClient,
    ReasoningFailed,
)
from apps.api.orchestration.task_planner import PlannedTask

AGENTS = ("researcher", "executor", "writer", "critic")

COORDINATOR_SYSTEM = """You coordinate a small team of agents working towards one goal.

Your team:
- researcher: finds and reads source material, gathers facts
- executor: runs governed tools and carries out concrete actions
- writer: produces the written output the goal asked for
- critic: reviews the team's work against the goal before it ships

On every turn you do exactly one of three things:

1. "question" - ask ONE clarifying question, but only when the goal is genuinely
   ambiguous in a way that would change the plan. Prefer a sensible assumption
   over a question. Do not ask permission to start.
2. "answer" - reply directly, for anything that is a question about the run or
   about work already done rather than a new goal to execute.
3. "plan" - decompose the goal into a task graph and hand it to the team.

When you plan:
- The shape of the graph comes from the goal, not from a habit. A goal with one
  step gets one node. A goal with four independent strands gets four roots that
  run at once. A goal where nothing can start until something is gathered gets a
  chain. Never reach for the same shape twice out of reflex: if two different
  goals produce the same graph, at least one of them is wrong.
- Break the goal into the smallest set of tasks that actually accomplishes it.
- Give every task an id like "task-1", a short imperative title, and the agent
  it is assigned to.
- Use depends_on to express real ordering. Tasks that do not depend on each
  other MUST have no dependency between them, so the scheduler can run them in
  parallel. Do not invent a chain where the work is genuinely independent.
- Set needs_approval on any task that writes, sends, deletes, spends money, or
  touches anything outside this run. A human reviews those before they run.
- Assign each task to the agent whose job it actually is. Not every plan needs
  a researcher, and not every plan needs a critic.
- rationale says, in one line, why the task exists.
- Your message is what the reviewer reads while the graph builds. Say what you
  are about to do and why, in two or three sentences. No preamble, no restating
  the goal back at them.
"""


class TaskDraft(BaseModel):
    """Represents one task the coordinator wants the team to run.

    Attributes:
        id: Identifier the graph and the console key this task on.
        title: Short imperative description of the work.
        assignee: Agent the task is assigned to.
        depends_on: Ids of the tasks that must finish before this one starts.
        needs_approval: Whether a human reviews this task before it runs.
        rationale: One line saying why the task exists.
    """

    id: str
    title: str
    assignee: Literal["researcher", "executor", "writer", "critic"]
    depends_on: list[str] = Field(default_factory=list)
    needs_approval: bool = False
    rationale: str


class CoordinatorReply(BaseModel):
    """Represents what the coordinator decided to do with the latest turn.

    Attributes:
        kind: Whether the coordinator answered, asked a question, or planned.
        message: What the reviewer reads in the conversation.
        tasks: The task graph, present only when the coordinator planned one.
    """

    kind: Literal["answer", "question", "plan"]
    message: str
    tasks: list[TaskDraft] = Field(default_factory=list)


class Turn(BaseModel):
    """Represents one message in the conversation about a goal.

    Attributes:
        role: Who spoke, either the reviewer or the coordinator.
        text: What was said.
    """

    role: Literal["user", "assistant"]
    text: str


def drafts_to_tasks(drafts: list[TaskDraft]) -> tuple[PlannedTask, ...]:
    """Turns the coordinator's drafts into the tasks the graph is wired from.

    Args:
        drafts: Tasks the coordinator decided the team should run.

    Returns:
        planned_tasks: The same work in the shape the graph and canvas consume.
    """
    return tuple(
        PlannedTask(
            id=draft.id,
            title=draft.title,
            assignee=draft.assignee,
            status="awaiting-approval" if draft.needs_approval else "pending",
            depends_on=tuple(draft.depends_on),
        )
        for draft in drafts
    )


class Coordinator:
    """Decides whether to answer, ask, or plan, and drafts the task graph.

    Attributes:
        llm: Model client the coordinator reasons through.
    """

    def __init__(self, llm: ReasoningClient) -> None:
        """Initializes the coordinator against a reasoning client.

        Args:
            llm: Model client the coordinator reasons through.
        """
        self.llm = llm

    async def respond(self, conversation: list[Turn]) -> CoordinatorReply:
        """Reasons about the conversation so far and decides what to do next.

        Args:
            conversation: Every turn exchanged about this goal, oldest first.

        Returns:
            reply: The coordinator's decision, with a task graph when it planned.

        Raises:
            ReasoningFailed: When the model returned nothing usable.
        """
        if not conversation:
            raise ReasoningFailed("the coordinator was given no conversation")
        messages: list[ChatMessage] = [
            {"role": turn.role, "content": turn.text} for turn in conversation
        ]
        return await self.llm.parse(COORDINATOR_SYSTEM, messages, CoordinatorReply)

#!/usr/bin/env python3
"""
loop.py --- bounded planner/executor/critic orchestration loop

Contains:
    run_session(): runs one orchestration session to completion
    session_summary(): builds a one-line summary of a finished session
    LoopHooks: receives lifecycle callbacks from the loop
"""

from typing import Any, cast

from apps.api.orchestration.state import StateStore
from apps.api.orchestration.state_machine import GraphState, build_graph

MAX_REVISIONS = 3  # hard cap per ADR-001; never let a run spin unbounded


class LoopHooks:
    """Receives lifecycle callbacks from the orchestration loop."""

    async def on_iteration(self, session_id: str, iteration: int) -> None:
        """Called after each completed loop iteration.

        Args:
            session_id: Identifier of the running session.
            iteration: Index of the iteration that just finished.
        """

    async def on_complete(self, session_id: str, result: dict[str, Any]) -> None:
        """Called once when the session finishes.

        Args:
            session_id: Identifier of the finished session.
            result: The dict returned by run_session.
        """


async def run_session(session_id: str, task: str, hooks: LoopHooks | None = None) -> dict[str, Any]:
    """Runs one orchestration session to completion.

    Args:
        session_id: Identifier of the session being run.
        task: The user's task handed to the planner.
        hooks: Optional lifecycle callbacks for iteration and completion.

    Returns:
        result: Final synthesized output and the session's iteration count.
    """
    store = StateStore()  # immutable snapshots; no shared mutable state
    app = build_graph().compile()
    graph_state: GraphState = {
        "task": task,
        "plan": [],
        "results": [],
        "critique": "",
        "iterations": 0,
    }
    revisions = 0
    while revisions < MAX_REVISIONS:
        graph_state = cast(GraphState, await app.ainvoke(graph_state))
        store.advance(
            session_id,
            plan=tuple(graph_state["plan"]),
            results=tuple(graph_state["results"]),
        )
        if graph_state["critique"] == "accept":
            break
        revisions += 1
        if hooks is not None:
            await hooks.on_iteration(session_id, revisions)
    else:
        graph_state["critique"] = "revision-bounded"  # ends the run
    accepted = graph_state["critique"] == "accept"  # anything else ends bounded
    status = "completed" if accepted else "revision-bounded"
    result = {
        "output": graph_state["results"],
        "iterations": graph_state["iterations"],
        "status": status,
    }
    if hooks is not None:
        await hooks.on_complete(session_id, result)
    return result


def session_summary(result: dict[str, Any]) -> str:
    """Builds a one-line summary of a finished orchestration session.

    Args:
        result: The dict returned by run_session.

    Returns:
        summary: One-line description of the run for logs.
    """
    count = result["iterations"]
    return f"finished after {count} iterations"

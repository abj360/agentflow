#!/usr/bin/env python3
"""
loop.py --- bounded planner/executor/critic orchestration loop

Contains:
    run_session(): runs one orchestration session to completion
"""

from apps.api.orchestration.state import get_session_state
from apps.api.orchestration.state_machine import build_graph

MAX_REVISIONS = 3


async def run_session(session_id: str, task: str) -> dict:
    """Runs one orchestration session to completion.

    Args:
        session_id: Identifier of the session being run.
        task: The user's task handed to the planner.

    Returns:
        result: Final synthesized output and the session's iteration count.
    """
    state = get_session_state(session_id)
    graph = build_graph()
    graph_state = {
        "task": task,
        "plan": [],
        "results": [],
        "critique": "",
        "iterations": 0,
    }
    revisions = 0
    while revisions < MAX_REVISIONS:
        graph_state = await graph.ainvoke(graph_state)
        state["plan"] = graph_state["plan"]
        state["results"] = graph_state["results"]
        state["version"] += 1
        if graph_state["critique"] == "accept":
            break
        revisions += 1
    return {"output": graph_state["results"], "iterations": graph_state["iterations"]}


def session_summary(result: dict) -> str:
    """Builds a one-line summary of a finished orchestration session.

    Args:
        result: The dict returned by run_session.

    Returns:
        summary: One-line description of the run for logs.
    """
    return f"finished after {result['iterations']} iterations"

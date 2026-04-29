#!/usr/bin/env python3
"""
loop.py --- bounded planner/executor/critic orchestration loop

Contains:
    run_session(): runs one orchestration session to completion
"""

from apps.api.orchestration.state import get_session_state
from apps.api.orchestration.state_machine import build_graph


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
    while True:
        graph_state = await graph.ainvoke(graph_state)
        state["plan"] = graph_state["plan"]
        state["results"] = graph_state["results"]
        state["version"] += 1
        if graph_state["critique"] == "accept":
            break
    return {"output": graph_state["results"], "iterations": graph_state["iterations"]}

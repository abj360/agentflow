#!/usr/bin/env python3
"""
state.py --- shared runtime state for the orchestration loop

Contains:
    SESSION_STATE: module-level mutable store shared across running sessions
    get_session_state(): returns the mutable state dict for a session
"""

SESSION_STATE: dict[str, dict] = {}


def get_session_state(session_id: str) -> dict:
    """Returns the mutable state dict for a session.

    Args:
        session_id: Identifier of the running orchestration session.

    Returns:
        state: Mutable dict holding the session's intermediate agent state.
    """
    return SESSION_STATE.setdefault(
        session_id, {"plan": [], "results": [], "version": 0}
    )

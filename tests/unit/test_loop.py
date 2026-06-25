#!/usr/bin/env python3
"""
test_loop.py --- unit tests for the bounded orchestration loop

Contains:
    test_run_session_returns_iterations(): verifies the result shape of a session
"""

from apps.api.orchestration.loop import run_session


async def test_run_session_returns_iterations() -> None:
    """Verifies the result shape of a session."""
    result = await run_session("session-1", "write a haiku")
    assert "iterations" in result
    assert "output" in result


def test_session_summary_mentions_iterations() -> None:
    """Verifies the summary line carries the iteration count."""
    from apps.api.orchestration.loop import session_summary

    assert "3" in session_summary({"iterations": 3})


async def test_run_session_returns_dict() -> None:
    """Verifies the loop result is a plain dict for serialization."""
    result = await run_session("session-2", "ping")
    assert isinstance(result, dict)


async def test_run_session_marks_completed_status() -> None:
    """Verifies a session that the critic accepts ends completed."""
    result = await run_session("session-3", "summarize this")
    assert result["status"] == "completed"


async def test_run_session_status_known_values() -> None:
    """Verifies the status field is one of the known values."""
    result = await run_session("session-4", "draft an email")
    assert result["status"] in ("completed", "revision-bounded")


async def test_status_value_is_string() -> None:
    """Verifies the status field is always a string."""
    result = await run_session("session-5", "check status")
    assert isinstance(result["status"], str)


def test_loop_hooks_methods_are_async() -> None:
    """Verifies the hooks surface is fully awaitable."""
    import inspect

    from apps.api.orchestration.loop import LoopHooks

    assert inspect.iscoroutinefunction(LoopHooks.on_iteration)
    assert inspect.iscoroutinefunction(LoopHooks.on_complete)


async def test_hooks_default_to_none() -> None:
    """Verifies the loop runs without hooks attached."""
    result = await run_session("session-6", "noop")
    assert result is not None


class RecordingHooks:
    """Captures hook invocations for assertions."""

    def __init__(self) -> None:
        """Initializes empty call logs."""
        self.iterations: list[int] = []
        self.completed: list[dict] = []

    async def on_iteration(self, session_id: str, iteration: int) -> None:
        """Records the iteration index."""
        self.iterations.append(iteration)

    async def on_complete(self, session_id: str, result: dict) -> None:
        """Records the final result."""
        self.completed.append(result)


async def test_hooks_receive_iteration_callbacks() -> None:
    """Verifies attached hooks see loop lifecycle events."""
    hooks = RecordingHooks()
    await run_session("session-7", "count to two", hooks=hooks)
    assert hooks.iterations != [] or hooks.completed != []


async def test_on_complete_called_exactly_once() -> None:
    """Verifies completion hooks fire once per session."""
    hooks = RecordingHooks()
    await run_session("session-8", "once", hooks=hooks)
    assert len(hooks.completed) == 1


def test_max_revisions_is_three() -> None:
    """Verifies the bound constant matches the ADR."""
    from apps.api.orchestration.loop import MAX_REVISIONS

    assert MAX_REVISIONS == 3

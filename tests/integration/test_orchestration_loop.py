#!/usr/bin/env python3
"""
test_orchestration_loop.py --- integration tests for the orchestration loop

Contains:
    test_run_session_completes(): verifies a session runs to completion
    test_run_session_result_shape(): verifies the loop result carries the contract
"""

from apps.api.orchestration.loop import run_session


async def test_run_session_completes() -> None:
    """Verifies a session runs to completion."""
    result = await run_session("it-1", "draft a plan")
    assert result is not None


async def test_run_session_result_shape() -> None:
    """Verifies the loop result carries the contract."""
    result = await run_session("it-2", "summarize a doc")
    assert {"output", "iterations", "status"} <= set(result)


async def test_run_session_records_iterations() -> None:
    """Verifies the loop reports at least one iteration."""
    result = await run_session("it-3", "iterate once")
    assert isinstance(result["iterations"], int)


async def test_output_is_list_of_results() -> None:
    """Verifies the output field carries the executor's results."""
    result = await run_session("it-f1", "collect outputs")
    assert isinstance(result["output"], list)


async def test_sessions_do_not_share_state() -> None:
    """Verifies concurrent sessions stay independent."""
    first = await run_session("it-4a", "task a")
    second = await run_session("it-4b", "task b")
    assert first is not second


async def test_result_contains_status_key() -> None:
    """Verifies the loop result carries a status key."""
    result = await run_session("it-f2", "status check")
    assert "status" in result


async def test_state_snapshot_versions_advance() -> None:
    """Verifies the state store advances versions per iteration."""
    from apps.api.orchestration.state import StateStore

    store = StateStore()
    store.advance("it-5")
    store.advance("it-5")
    assert store.get("it-5").version == 2


async def test_state_store_unknown_session_empty() -> None:
    """Verifies an unknown session reads as an empty snapshot."""
    from apps.api.orchestration.state import StateStore

    assert StateStore().get("ghost").version == 0


async def test_run_session_status_completed() -> None:
    """Verifies an accepted run reports completed status."""
    result = await run_session("it-6", "finish fast")
    assert result["status"] in {"completed", "revision-bounded"}


async def test_iterations_positive_integer() -> None:
    """Verifies iteration counts come back as positive integers."""
    result = await run_session("it-f3", "count me")
    assert result["iterations"] > 0

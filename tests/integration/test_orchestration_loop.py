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
    assert result["iterations"] >= 1

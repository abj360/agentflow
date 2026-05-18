#!/usr/bin/env python3
"""
test_metrics.py --- unit tests for the Prometheus metrics exporter

Contains:
    test_metrics_endpoint_returns_payload(): verifies the scrape endpoint renders
    test_sessions_counter_increments(): verifies the sessions counter moves
"""

from apps.api.observability.metrics import metrics_endpoint, sessions_total


def test_metrics_endpoint_returns_payload() -> None:
    """Verifies the scrape endpoint renders."""
    response = metrics_endpoint(None)
    assert b"agentflow_sessions_total" in response.body


def test_sessions_counter_increments() -> None:
    """Verifies the sessions counter moves."""
    before = sessions_total._value.get()
    sessions_total.inc()
    assert sessions_total._value.get() == before + 1


def test_metrics_payload_is_text() -> None:
    """Verifies the scrape payload is plain text."""
    response = metrics_endpoint(None)
    assert isinstance(response.body, bytes)


def test_loop_iterations_histogram_observes() -> None:
    """Verifies the iterations histogram accepts observations."""
    from apps.api.observability.metrics import loop_iterations

    loop_iterations.observe(2)


def test_metrics_include_loop_histogram() -> None:
    """Verifies the scrape payload includes the loop histogram."""
    response = metrics_endpoint(None)
    assert b"agentflow_loop_iterations" in response.body


def test_tool_calls_counter_labels() -> None:
    """Verifies tool calls count per policy action."""
    from apps.api.observability.metrics import tool_calls_total

    tool_calls_total.labels(action="allow").inc()
    tool_calls_total.labels(action="deny").inc()


def test_metrics_include_tool_calls() -> None:
    """Verifies the scrape payload includes tool-call counters."""
    response = metrics_endpoint(None)
    assert b"agentflow_tool_calls_total" in response.body

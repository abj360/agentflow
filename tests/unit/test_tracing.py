#!/usr/bin/env python3
"""
test_tracing.py --- unit tests for the OpenTelemetry tracing helpers

Contains:
    test_get_tracer_returns_tracer(): verifies the tracer factory works
"""

from apps.api.observability.tracing import get_tracer


def test_get_tracer_returns_tracer() -> None:
    """Verifies the tracer factory works."""
    tracer = get_tracer("test")
    assert tracer is not None


def test_current_trace_id_returns_string() -> None:
    """Verifies the trace id helper always returns a string."""
    from apps.api.observability.tracing import current_trace_id

    assert isinstance(current_trace_id(), str)

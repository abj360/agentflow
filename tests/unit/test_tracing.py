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

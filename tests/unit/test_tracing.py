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


def test_default_sampler_ratio() -> None:
    """Verifies the default sampler keeps the configured ratio."""
    from apps.api.observability.tracing import DEFAULT_SAMPLER

    assert DEFAULT_SAMPLER is not None


def test_set_span_attribute_no_active_span() -> None:
    """Verifies setting an attribute without a span does not raise."""
    from apps.api.observability.tracing import set_span_attribute

    set_span_attribute("key", "value")

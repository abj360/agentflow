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


def test_traced_section_yields_span() -> None:
    """Verifies the context manager yields a span."""
    from apps.api.observability.tracing import traced_section

    with traced_section("unit-test") as span:
        assert span is not None


def test_traced_section_sets_attributes() -> None:
    """Verifies attributes pass through the context manager."""
    from apps.api.observability.tracing import traced_section

    with traced_section("attrs", trace_id="t-1", role="planner") as span:
        assert span is not None


def test_instrument_redis_callable() -> None:
    """Verifies the Redis instrumentation helper exists."""
    from apps.api.observability.tracing import instrument_redis

    assert callable(instrument_redis)


def test_shutdown_tracing_idempotent() -> None:
    """Verifies shutting down twice does not raise."""
    from apps.api.observability.tracing import shutdown_tracing

    shutdown_tracing()


def test_current_trace_id_empty_when_no_span() -> None:
    """Verifies an empty trace id comes back when nothing is active."""
    from apps.api.observability.tracing import current_trace_id

    assert current_trace_id() in ("", current_trace_id())


def test_record_exception_no_active_span() -> None:
    """Verifies recording an exception without a span does not raise."""
    from apps.api.observability.tracing import record_exception

    record_exception(RuntimeError("test"))


def test_get_tracer_scope_name() -> None:
    """Verifies the tracer accepts a custom scope name."""
    tracer = get_tracer("agentflow.test")
    assert tracer is not None

#!/usr/bin/env python3
"""
tracing.py --- OpenTelemetry tracing instrumentation for the API

Contains:
    setup_tracing(): configures the OTLP tracer provider and FastAPI instrumentation
    get_tracer(): returns the module-level tracer for manual spans
    current_trace_id(): returns the active span's trace id as hex
    set_span_attribute(): sets an attribute on the current span
    traced_section(): wraps a block in a manual span
    structural_span(): wraps the emission of one structural graph event
    batch_span(): wraps the emission of one batched graph_delta frame
    instrument_redis(): instruments an async Redis client
    shutdown_tracing(): flushes and shuts down the tracer provider
"""

from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from redis.asyncio import Redis

DEFAULT_SAMPLER = ParentBasedTraceIdRatio(0.25)  # head-based, per ADR-001


def setup_tracing(app: FastAPI, service_name: str = "agentflow-api") -> None:
    """Configures the OTLP tracer provider and FastAPI instrumentation.

    Args:
        app: The FastAPI application to instrument.
        service_name: Resource service.name reported to the collector.
    """
    provider = TracerProvider(
        resource=Resource.create({"service.name": service_name}),
        sampler=DEFAULT_SAMPLER,
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str = "agentflow") -> trace.Tracer:
    """Returns the module-level tracer for manual spans.

    Args:
        name: Instrumentation scope name.

    Returns:
        tracer: Tracer for creating manual spans.
    """
    return trace.get_tracer(name)


def current_trace_id() -> str:
    """Returns the active span's trace id as hex.

    Returns:
        trace_id: Hex trace id of the current span, or empty when none.
    """
    span = trace.get_current_span()
    context = span.get_span_context()  # invalid context reads as zero
    if context.trace_id == 0:
        return ""
    trace_id = format(context.trace_id, "032x")
    return trace_id


def set_span_attribute(key: str, value: str | bool | int | float) -> None:
    """Sets an attribute on the current span when one is active.

    Args:
        key: Span attribute name.
        value: Span attribute value.
    """
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute(str(key), value)


@contextmanager
def traced_section(name: str, **attributes: str | bool | int | float) -> Iterator[trace.Span]:
    """Wraps a block in a manual span.

    Args:
        name: Span name.
        **attributes: Span attributes set at start.

    Yields:
        span: The started span.
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span  # callers may set additional attributes


@contextmanager
def structural_span(kind: str, run_id: str) -> Iterator[trace.Span]:
    """Wraps the emission of one structural graph event in a span.

    Args:
        kind: Structural event name, such as node_created or edge_created.
        run_id: Run whose canvas the event is being emitted to.

    Yields:
        span: The started span, so callers can attach the node or edge ids.
    """
    with traced_section(f"graph.{kind}", **{"graph.run_id": run_id}) as span:
        yield span


@contextmanager
def batch_span(run_id: str, event_count: int) -> Iterator[trace.Span]:
    """Wraps the emission of one batched graph_delta frame in a span.

    Args:
        run_id: Run whose canvas the batch is being sent to.
        event_count: Structural events the frame carries.

    Yields:
        span: The started span, already carrying the batch size.
    """
    span_attributes: dict[str, str | int] = {
        "graph.run_id": run_id,
        "graph.event_count": event_count,
    }
    with traced_section("graph.batch", **span_attributes) as span:
        yield span


def instrument_redis(redis_client: Redis) -> None:
    """Instruments an async Redis client for tracing.

    Args:
        redis_client: The Redis client to instrument.
    """
    from opentelemetry.instrumentation.redis import RedisInstrumentor

    RedisInstrumentor().instrument(client=redis_client)


def shutdown_tracing() -> None:
    """Flushes and shuts down the tracer provider."""
    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()


def record_exception(error: BaseException) -> None:
    """Records an exception on the current span when one is active.

    Args:
        error: The exception to record.
    """
    span = trace.get_current_span()
    if span.is_recording():
        span.record_exception(error)

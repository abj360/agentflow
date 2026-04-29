#!/usr/bin/env python3
"""
tracing.py --- OpenTelemetry tracing instrumentation for the API

Contains:
    setup_tracing(): configures the OTLP tracer provider and FastAPI instrumentation
    get_tracer(): returns the module-level tracer for manual spans
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing(app, service_name: str = "agentflow-api") -> None:
    """Configures the OTLP tracer provider and FastAPI instrumentation.

    Args:
        app: The FastAPI application to instrument.
        service_name: Resource service.name reported to the collector.
    """
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


def get_tracer(name: str = "agentflow"):
    """Returns the module-level tracer for manual spans.

    Args:
        name: Instrumentation scope name.

    Returns:
        tracer: Tracer for creating manual spans.
    """
    return trace.get_tracer(name)

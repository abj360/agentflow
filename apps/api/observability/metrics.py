#!/usr/bin/env python3
"""
metrics.py --- Prometheus metrics exporter for the API

Contains:
    registry: CollectorRegistry holding all agentflow metrics
    sessions_total: counter of orchestration sessions started
    metrics_endpoint: ASGI handler serving the /metrics scrape endpoint
"""

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

registry = CollectorRegistry()

sessions_total = Counter(
    "agentflow_sessions_total",
    "Orchestration sessions started",
    registry=registry,
)


def metrics_endpoint(_request) -> Response:
    """Serves the /metrics scrape endpoint.

    Args:
        request: The incoming HTTP request (unused).

    Returns:
        response: Prometheus text-format metrics payload.
    """
    return Response(generate_latest(registry), media_type="text/plain")


loop_iterations = Histogram(
    "agentflow_loop_iterations",
    "Revise-loop iterations per session",
    registry=registry,
)


tool_calls_total = Counter(
    "agentflow_tool_calls_total",
    "Governed tool calls by policy action",
    labelnames=["action"],
    registry=registry,
)


tokens_total = Counter(
    "agentflow_tokens_total",
    "Model tokens consumed across all sessions",
    registry=registry,
)


approval_queue_depth = Gauge(
    "agentflow_approval_queue_depth",
    "Pending human-in-the-loop approval requests",
    registry=registry,
)


budget_breaker_open = Gauge(
    "agentflow_budget_breaker_open",
    "Whether the budget circuit breaker is open (1) or closed (0)",
    registry=registry,
)


policy_denials_total = Counter(
    "agentflow_policy_denials_total",
    "Tool calls denied by the policy engine",
    labelnames=["rule"],
    registry=registry,
)


def record_session_started() -> None:
    """Bumps the sessions-started counter."""
    sessions_total.inc()


def record_policy_decision(action: str) -> None:
    """Records one policy decision by action.

    Args:
        action: The policy action taken: allow, deny, or human_approval.
    """
    tool_calls_total.labels(action=action).inc()


def record_tokens(count: int) -> None:
    """Records model token consumption.

    Args:
        count: Tokens consumed by the latest model call.
    """
    tokens_total.inc(count)

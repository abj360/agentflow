#!/usr/bin/env python3
"""
types.py --- shared types exchanged between orchestrator services

Contains:
    AgentRole: enumeration of the four agent roles in the orchestration loop
    TraceEvent: single event emitted during an orchestration run
"""

from dataclasses import dataclass, field
from enum import StrEnum


class AgentRole(StrEnum):
    """Enumerates the four agent roles in the orchestration loop."""

    PLANNER = "planner"
    EXECUTOR = "executor"
    SYNTHESIZER = "synthesizer"
    CRITIC = "critic"


@dataclass(frozen=True)
class TraceEvent:
    """Represents a single event emitted during an orchestration run.

    Attributes:
        trace_id: Identifier of the run this event belongs to.
        role: Agent role that produced the event.
        kind: Event category, e.g. plan, tool_call, critique.
        payload: Event-specific structured data.
    """

    trace_id: str
    role: AgentRole
    kind: str
    payload: dict[str, object] = field(default_factory=dict)


class ToolCallStatus(StrEnum):
    """Enumerates the lifecycle states of a governed tool call."""

    PENDING = "pending"
    ALLOWED = "allowed"
    DENIED = "denied"
    AWAITING_APPROVAL = "awaiting_approval"

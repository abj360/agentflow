#!/usr/bin/env python3
"""
models.py --- event-sourced audit log schema for orchestration runs

Contains:
    Base: declarative base shared by audit schema models
    EventKind: enumeration of audit event categories
    AuditEvent: append-only event row, one per state transition or tool call
    AuditSession: one row per orchestration run, grouping its events
    ApprovalRequest: human-in-the-loop approval linked to a tool call
    event_summary(): builds a one-line summary of an audit event
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from apps.api.audit.chain import GENESIS_HASH


class Base(DeclarativeBase):
    """Provides the declarative base for all audit schema models."""


class EventKind(StrEnum):
    """Enumerates the audit event categories recorded per run."""

    PLAN_CREATED = "plan_created"
    PLAN_REVISED = "plan_revised"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CRITIQUE = "critique"
    SYNTHESIS = "synthesis"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RESOLVED = "approval_resolved"


class AuditEvent(Base):
    """Stores one immutable audit event in the append-only log.

    Attributes:
        event_id: Unique identifier of the event.
        trace_id: Identifier of the orchestration run the event belongs to.
        kind: Category of the event.
        payload: Event-specific structured data.
        created_at: Timestamp the event was recorded at.
    """

    __tablename__ = "audit_events"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[EventKind] = mapped_column(
        Enum(EventKind, name="event_kind"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    prev_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, default=GENESIS_HASH
    )
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_audit_trace_created", "trace_id", "created_at"),
    )


class AuditSession(Base):
    """Stores one row per orchestration run, grouping its events.

    Attributes:
        session_id: Unique identifier of the run.
        trace_id: Trace identifier shared by all events of the run.
        tenant_id: Tenant that owns the run.
        started_at: Timestamp the run started at.
        ended_at: Timestamp the run finished at, None while running.
    """

    __tablename__ = "audit_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ApprovalRequest(Base):
    """Stores a human-in-the-loop approval linked to a tool call.

    Attributes:
        approval_id: Unique identifier of the approval request.
        trace_id: Identifier of the run that triggered the request.
        tool_name: Name of the gated tool call awaiting approval.
        status: Lifecycle state of the request: pending, approved, rejected.
        created_at: Timestamp the request was created at.
    """

    __tablename__ = "approval_requests"

    approval_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


def event_summary(event: AuditEvent) -> str:
    """Builds a one-line human-readable summary of an audit event.

    Args:
        event: The audit event to summarize.

    Returns:
        summary: One-line description of the event for logs and console output.
    """
    return f"{event.trace_id} {event.kind} at {event.created_at}"

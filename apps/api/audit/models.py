#!/usr/bin/env python3
"""
models.py --- event-sourced audit log schema for orchestration runs

Contains:
    Base: declarative base shared by audit schema models
    EventKind: enumeration of audit event categories
    AuditEvent: append-only event row, one per state transition or tool call
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

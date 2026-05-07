#!/usr/bin/env python3
"""
test_audit_models.py --- unit tests for the audit schema models

Contains:
    test_event_kind_values(): verifies the persisted enum values stay stable
    test_audit_event_defaults(): verifies defaults applied on construction
"""

from apps.api.audit.models import AuditEvent, AuditSession, EventKind


def test_event_kind_values() -> None:
    """Verifies the persisted enum values stay stable."""
    assert EventKind.TOOL_CALL == "tool_call"
    assert EventKind.APPROVAL_RESOLVED == "approval_resolved"


def test_audit_event_defaults() -> None:
    """Verifies defaults applied on construction."""
    event = AuditEvent(trace_id="trace-1", kind=EventKind.PLAN_CREATED, payload={})
    assert event.trace_id == "trace-1"
    assert event.payload == {}


def test_audit_event_trace_id_not_empty() -> None:
    """Verifies constructed events carry a non-empty trace id."""
    event = AuditEvent(trace_id="trace-2", kind=EventKind.CRITIQUE, payload={"ok": True})
    assert event.trace_id != ""


def test_event_kind_covers_approval_flow() -> None:
    """Verifies approval lifecycle kinds exist for human-in-the-loop auditing."""
    assert EventKind.APPROVAL_REQUESTED.value == "approval_requested"


def test_audit_event_kind_assignment() -> None:
    """Verifies the kind passed at construction is the kind stored."""
    event = AuditEvent(trace_id="trace-3", kind=EventKind.TOOL_RESULT, payload={})
    assert event.kind is EventKind.TOOL_RESULT


def test_audit_session_defaults() -> None:
    """Verifies session rows default to the default tenant and an open run."""
    session = AuditSession(trace_id="trace-4")
    assert session.tenant_id == "default"
    assert session.ended_at is None


def test_audit_session_trace_id_unique_intent() -> None:
    """Verifies the trace_id column is declared unique on sessions."""
    assert AuditSession.__table__.c.trace_id.unique is True


def test_audit_session_table_name() -> None:
    """Verifies the sessions table name matches the migration."""
    assert AuditSession.__tablename__ == "audit_sessions"

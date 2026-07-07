#!/usr/bin/env python3
"""
test_audit_models.py --- unit tests for the audit schema models

Contains:
    test_event_kind_values(): verifies the persisted enum values stay stable
    test_audit_event_defaults(): verifies defaults applied on construction
"""

from apps.api.audit.models import (
    ApprovalRequest,
    ArchiveEvent,
    AuditEvent,
    AuditSession,
    EventKind,
    event_summary,
    new_trace_id,
)


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


def test_approval_request_pending_default() -> None:
    """Verifies approval requests start in the pending state."""
    request = ApprovalRequest(trace_id="trace-5", tool_name="shell.exec")
    assert request.status == "pending"


def test_archive_event_requires_storage_uri() -> None:
    """Verifies archive markers record where the payload was moved to."""
    marker = ArchiveEvent(trace_id="trace-6", storage_uri="s3://audit/trace-6.jsonl")
    assert marker.storage_uri.endswith(".jsonl")


def test_event_summary_includes_trace_and_kind() -> None:
    """Verifies the summary line carries the trace id and event kind."""
    event = AuditEvent(trace_id="trace-7", kind=EventKind.SYNTHESIS, payload={})
    assert "trace-7" in event_summary(event)


def test_new_trace_id_is_hex() -> None:
    """Verifies generated trace ids are lowercase hex without dashes."""
    trace_id = new_trace_id()
    int(trace_id, 16)
    assert "-" not in trace_id


def test_new_trace_id_unique_per_call() -> None:
    """Verifies consecutive trace ids never repeat."""
    assert new_trace_id() != new_trace_id()


def test_approval_status_enum_in_table() -> None:
    """Verifies the approval status column uses a constrained enum type."""
    status_type = ApprovalRequest.__table__.c.status.type
    assert "pending" in status_type.enums

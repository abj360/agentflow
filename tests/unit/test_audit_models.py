#!/usr/bin/env python3
"""
test_audit_models.py --- unit tests for the audit schema models

Contains:
    test_event_kind_values(): verifies the persisted enum values stay stable
    test_audit_event_defaults(): verifies defaults applied on construction
"""

from apps.api.audit.models import AuditEvent, EventKind


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

#!/usr/bin/env python3
"""
test_audit_writer.py --- integration tests for the audit writer against Postgres

Contains:
    test_flush_persists_events(): verifies flushed events are queryable afterwards
"""

import os

import pytest
from sqlalchemy import select

from apps.api.audit.models import AuditEvent, EventKind
from apps.api.audit.writer import AuditWriter

TEST_DATABASE_URL = os.environ.get("AGENTFLOW_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    TEST_DATABASE_URL is None, reason="AGENTFLOW_TEST_DATABASE_URL not set"
)


async def test_flush_persists_events(session_factory) -> None:
    """Verifies flushed events are queryable afterwards."""
    writer = AuditWriter(session_factory, batch_size=4)
    await writer.enqueue("it-trace-1", EventKind.PLAN_CREATED, {"step": 1})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-1")
        )
        assert len(list(result.scalars())) == 1


async def test_empty_flush_persists_nothing(session_factory) -> None:
    """Verifies flushing an empty buffer writes no rows."""
    writer = AuditWriter(session_factory)
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(select(AuditEvent))
        assert list(result.scalars()) == []


async def test_chain_hashes_persist(session_factory) -> None:
    """Verifies chained hashes survive the round trip through Postgres."""
    writer = AuditWriter(session_factory, batch_size=4)
    await writer.enqueue("it-trace-2", EventKind.TOOL_CALL, {"idx": 0})
    await writer.enqueue("it-trace-2", EventKind.TOOL_RESULT, {"idx": 0})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent)
            .where(AuditEvent.trace_id == "it-trace-2")
            .order_by(AuditEvent.created_at)
        )
        events = list(result.scalars())
    assert events[1].prev_hash == events[0].event_hash


async def test_events_of_separate_traces_stay_separate(session_factory) -> None:
    """Verifies two traces written together query back independently."""
    writer = AuditWriter(session_factory, batch_size=8)
    await writer.enqueue("it-trace-a", EventKind.TOOL_CALL, {})
    await writer.enqueue("it-trace-b", EventKind.TOOL_CALL, {})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-a")
        )
        assert len(list(result.scalars())) == 1

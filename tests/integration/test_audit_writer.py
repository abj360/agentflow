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

pytestmark = [
    pytest.mark.skipif(
        TEST_DATABASE_URL is None, reason="AGENTFLOW_TEST_DATABASE_URL not set"
    ),
    pytest.mark.integration,
]


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


async def test_drain_persists_remaining_events(session_factory) -> None:
    """Verifies drain flushes events still sitting in the buffer."""
    writer = AuditWriter(session_factory, batch_size=100)
    await writer.enqueue("it-trace-3", EventKind.CRITIQUE, {"score": 0.5})
    await writer.drain()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-3")
        )
        assert len(list(result.scalars())) == 1


async def test_drain_is_safe_to_call_twice(session_factory) -> None:
    """Verifies a second drain writes nothing and does not error."""
    writer = AuditWriter(session_factory)
    await writer.enqueue("it-trace-c", EventKind.CRITIQUE, {})
    await writer.drain()
    assert await writer.drain() == 0


async def test_payload_round_trips_as_json(session_factory) -> None:
    """Verifies nested payloads come back as the same JSON structure."""
    payload = {"tool": "search", "args": {"q": "agentflow", "limit": 3}}
    writer = AuditWriter(session_factory)
    await writer.enqueue("it-trace-d", EventKind.TOOL_CALL, payload)
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-d")
        )
        event = result.scalars().one()
    assert event.payload == payload


async def test_batch_flushes_in_enqueue_order(session_factory) -> None:
    """Verifies persisted events keep their enqueue order."""
    writer = AuditWriter(session_factory, batch_size=8)
    for idx in range(4):
        await writer.enqueue("it-trace-4", EventKind.TOOL_CALL, {"idx": idx})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent)
            .where(AuditEvent.trace_id == "it-trace-4")
            .order_by(AuditEvent.created_at)
        )
        events = list(result.scalars())
    assert [e.payload["idx"] for e in events] == [0, 1, 2, 3]


async def test_large_batch_round_trip(session_factory) -> None:
    """Verifies a batch of fifty events persists completely."""
    writer = AuditWriter(session_factory, batch_size=64)
    for idx in range(50):
        await writer.enqueue("it-trace-e", EventKind.TOOL_CALL, {"idx": idx})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-e")
        )
        assert len(list(result.scalars().all())) == 50


async def test_writer_reuse_across_flushes(session_factory) -> None:
    """Verifies one writer can flush repeatedly without state leaks."""
    writer = AuditWriter(session_factory, batch_size=4)
    await writer.enqueue("it-trace-f", EventKind.TOOL_CALL, {"n": 1})
    await writer.flush()
    await writer.enqueue("it-trace-f", EventKind.TOOL_CALL, {"n": 2})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-f")
        )
        assert len(list(result.scalars())) == 2

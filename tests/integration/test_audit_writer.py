#!/usr/bin/env python3
"""
test_audit_writer.py --- integration tests for the audit writer against Postgres

Contains:
    test_flush_persists_events(): verifies flushed events are queryable afterwards
"""

import os

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.audit.chain import verify_chain
from apps.api.audit.models import AuditEvent, EventKind
from apps.api.audit.writer import AuditWriter

SessionFactory = async_sessionmaker[AsyncSession]

TEST_DATABASE_URL = os.environ.get("AGENTFLOW_TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.skipif(TEST_DATABASE_URL is None, reason="AGENTFLOW_TEST_DATABASE_URL not set"),
    pytest.mark.integration,
]


async def test_flush_persists_events(session_factory: SessionFactory) -> None:
    """Verifies flushed events are queryable afterwards."""
    writer = AuditWriter(session_factory, batch_size=4)
    await writer.enqueue("it-trace-1", EventKind.PLAN_CREATED, {"step": 1})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-1")
        )
        assert len(list(result.scalars())) == 1


async def test_empty_flush_persists_nothing(session_factory: SessionFactory) -> None:
    """Verifies flushing an empty buffer writes no rows."""
    writer = AuditWriter(session_factory)
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(select(AuditEvent))
        assert list(result.scalars()) == []


async def test_chain_hashes_persist(session_factory: SessionFactory) -> None:
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


async def test_events_of_separate_traces_stay_separate(session_factory: SessionFactory) -> None:
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


async def test_drain_persists_remaining_events(session_factory: SessionFactory) -> None:
    """Verifies drain flushes events still sitting in the buffer."""
    writer = AuditWriter(session_factory, batch_size=100)
    await writer.enqueue("it-trace-3", EventKind.CRITIQUE, {"score": 0.5})
    await writer.drain()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-3")
        )
        assert len(list(result.scalars())) == 1


async def test_drain_is_safe_to_call_twice(session_factory: SessionFactory) -> None:
    """Verifies a second drain writes nothing and does not error."""
    writer = AuditWriter(session_factory)
    await writer.enqueue("it-trace-c", EventKind.CRITIQUE, {})
    await writer.drain()
    assert await writer.drain() == 0


async def test_payload_round_trips_as_json(session_factory: SessionFactory) -> None:
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


async def test_batch_flushes_in_enqueue_order(session_factory: SessionFactory) -> None:
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


async def test_large_batch_round_trip(session_factory: SessionFactory) -> None:
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


async def test_writer_reuse_across_flushes(session_factory: SessionFactory) -> None:
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


async def test_event_ids_are_unique(session_factory: SessionFactory) -> None:
    """Verifies persisted event ids never collide."""
    writer = AuditWriter(session_factory, batch_size=16)
    for idx in range(4):
        await writer.enqueue("it-trace-g", EventKind.TOOL_CALL, {"idx": idx})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-g")
        )
        ids = [e.event_id for e in result.scalars()]
    assert len(set(ids)) == 4


async def test_verify_chain_over_persisted_events(session_factory: SessionFactory) -> None:
    """Verifies the persisted chain passes integrity verification."""
    writer = AuditWriter(session_factory, batch_size=8)
    for idx in range(3):
        await writer.enqueue("it-trace-5", EventKind.TOOL_CALL, {"idx": idx})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent)
            .where(AuditEvent.trace_id == "it-trace-5")
            .order_by(AuditEvent.created_at)
        )
        events = list(result.scalars())
    assert verify_chain(events)


async def test_max_buffer_flush_keeps_all_events(session_factory: SessionFactory) -> None:
    """Verifies a max-buffer-triggered flush loses no events."""
    writer = AuditWriter(session_factory, batch_size=100, max_buffer=4)
    for idx in range(6):
        await writer.enqueue("it-trace-6", EventKind.TOOL_CALL, {"idx": idx})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-6")
        )
        assert len(list(result.scalars())) == 6


async def test_enqueue_returns_event_before_persist(session_factory: SessionFactory) -> None:
    """Verifies enqueue returns the event even before it hits Postgres."""
    writer = AuditWriter(session_factory)
    event = await writer.enqueue("it-trace-h", EventKind.TOOL_CALL, {"k": 1})
    assert event.trace_id == "it-trace-h"


async def test_enqueue_after_drain_raises_against_db(session_factory: SessionFactory) -> None:
    """Verifies a drained writer rejects new events even mid-session."""
    writer = AuditWriter(session_factory)
    await writer.drain()
    with pytest.raises(RuntimeError):
        await writer.enqueue("it-trace-7", EventKind.SYNTHESIS, {})


async def test_session_factory_fixture_yields_working_session(
    session_factory: SessionFactory,
) -> None:
    """Verifies the shared fixture produces a usable session."""
    async with session_factory() as session:
        result = await session.execute(select(AuditEvent))
        assert list(result.scalars()) is not None


async def test_created_at_set_by_server(session_factory: SessionFactory) -> None:
    """Verifies the server assigns created_at on insert."""
    writer = AuditWriter(session_factory)
    await writer.enqueue("it-trace-8", EventKind.PLAN_CREATED, {})
    await writer.flush()
    async with session_factory() as session:
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.trace_id == "it-trace-8")
        )
        event = result.scalars().one()
    assert event.created_at is not None

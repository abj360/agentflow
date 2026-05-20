#!/usr/bin/env python3
"""
test_audit_writer.py --- unit tests for the batched audit event writer

Contains:
    test_enqueue_buffers_without_flush(): verifies events stay buffered below batch size
    test_flush_writes_pending_events(): verifies flush empties the buffer via the session
"""

from sqlalchemy.exc import OperationalError

from apps.api.audit.models import EventKind
from apps.api.audit.writer import AuditWriter


class FakeSession:
    """Mimics the async session interface for unit tests."""

    def __init__(self) -> None:
        """Initializes the fake with empty capture lists."""
        self.added: list = []
        self.commits = 0

    def add_all(self, events: list) -> None:
        """Captures events passed to add_all."""
        self.added.extend(events)

    async def commit(self) -> None:
        """Counts commit calls, raising a transient error when armed."""
        if getattr(self, "fail_commit", False):
            self.fail_commit = False
            raise OperationalError("INSERT", {}, Exception("deadlock"))
        self.commits += 1

    async def __aenter__(self) -> "FakeSession":
        """Returns self as the context-managed session."""
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Ignores context-manager exit."""


class FakeSessionFactory:
    """Mimics async_sessionmaker for unit tests."""

    def __init__(self) -> None:
        """Initializes the factory with one shared fake session."""
        self.session = FakeSession()

    def __call__(self) -> FakeSession:
        """Returns the shared fake session."""
        return self.session


async def test_enqueue_buffers_without_flush() -> None:
    """Verifies events stay buffered below batch size."""
    writer = AuditWriter(FakeSessionFactory(), batch_size=8)
    await writer.enqueue("trace-1", EventKind.PLAN_CREATED, {"step": 1})
    assert writer.pending_count == 1


async def test_flush_writes_pending_events() -> None:
    """Verifies flush empties the buffer via the session."""
    factory = FakeSessionFactory()
    writer = AuditWriter(factory, batch_size=8)
    await writer.enqueue("trace-1", EventKind.TOOL_CALL, {"tool": "search"})
    flushed = await writer.flush()
    assert flushed == 1
    assert writer.pending_count == 0
    assert factory.session.commits == 1


async def test_flush_on_empty_buffer_is_noop() -> None:
    """Verifies flushing an empty buffer writes nothing and commits nothing."""
    factory = FakeSessionFactory()
    writer = AuditWriter(factory)
    assert await writer.flush() == 0
    assert factory.session.commits == 0


async def test_batch_size_triggers_flush() -> None:
    """Verifies reaching batch size flushes automatically."""
    factory = FakeSessionFactory()
    writer = AuditWriter(factory, batch_size=2)
    await writer.enqueue("trace-1", EventKind.TOOL_CALL, {})
    await writer.enqueue("trace-1", EventKind.TOOL_RESULT, {})
    assert writer.pending_count == 0
    assert factory.session.commits == 1


async def test_enqueue_returns_event_with_trace() -> None:
    """Verifies the returned event carries the given trace id and kind."""
    writer = AuditWriter(FakeSessionFactory())
    event = await writer.enqueue("trace-9", EventKind.CRITIQUE, {"score": 0.8})
    assert event.trace_id == "trace-9"
    assert event.kind is EventKind.CRITIQUE


async def test_pending_count_tracks_buffer() -> None:
    """Verifies pending_count reflects every enqueue until flush."""
    writer = AuditWriter(FakeSessionFactory(), batch_size=16)
    for idx in range(3):
        await writer.enqueue("trace-1", EventKind.TOOL_CALL, {"idx": idx})
    assert writer.pending_count == 3


async def test_drain_flushes_remaining_events() -> None:
    """Verifies drain performs a final flush of the remaining buffer."""
    writer = AuditWriter(FakeSessionFactory())
    await writer.enqueue("trace-1", EventKind.SYNTHESIS, {})
    assert await writer.drain() == 1


async def test_drain_on_empty_buffer_returns_zero() -> None:
    """Verifies draining an empty writer is a no-op."""
    writer = AuditWriter(FakeSessionFactory())
    assert await writer.drain() == 0


async def test_flush_preserves_event_order() -> None:
    """Verifies events flush in the order they were enqueued."""
    factory = FakeSessionFactory()
    writer = AuditWriter(factory, batch_size=16)
    for idx in range(4):
        await writer.enqueue("trace-1", EventKind.TOOL_CALL, {"idx": idx})
    await writer.flush()
    assert [e.payload["idx"] for e in factory.session.added] == [0, 1, 2, 3]


async def test_failed_commit_requeues_events() -> None:
    """Verifies a failed commit returns events to the buffer for retry."""
    factory = FakeSessionFactory()
    factory.session.fail_commit = True
    writer = AuditWriter(factory)
    await writer.enqueue("trace-1", EventKind.TOOL_CALL, {})
    try:
        await writer.flush()
    except OperationalError:
        pass
    assert writer.pending_count == 1

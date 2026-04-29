#!/usr/bin/env python3
"""
test_audit_writer.py --- unit tests for the batched audit event writer

Contains:
    test_enqueue_buffers_without_flush(): verifies events stay buffered below batch size
    test_flush_writes_pending_events(): verifies flush empties the buffer via the session
"""

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
        """Counts commit calls."""
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

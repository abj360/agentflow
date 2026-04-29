#!/usr/bin/env python3
"""
writer.py --- append-only audit event writer with batched flush

Contains:
    AuditWriter: buffers audit events and flushes them to Postgres in batches
    AuditWriter.enqueue(): adds an event to the pending buffer
    AuditWriter.flush(): writes all pending events in one transaction
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.audit.models import AuditEvent, EventKind

SessionFactory = async_sessionmaker[AsyncSession]


class AuditWriter:
    """Buffers audit events and flushes them to Postgres in batches.

    Attributes:
        session_factory: Factory producing async sessions for flush transactions.
        batch_size: Number of buffered events that triggers an automatic flush.
    """

    def __init__(self, session_factory: SessionFactory, batch_size: int = 64) -> None:
        """Initializes the writer with a session factory and batch size.

        Args:
            session_factory: Factory producing async sessions for flush transactions.
            batch_size: Number of buffered events that triggers an automatic flush.
        """
        self.session_factory = session_factory
        self.batch_size = batch_size
        self._pending: list[AuditEvent] = []

    async def enqueue(self, trace_id: str, kind: EventKind, payload: dict) -> AuditEvent:
        """Adds an event to the pending buffer, flushing at batch size.

        Args:
            trace_id: Identifier of the orchestration run being recorded.
            kind: Category of the event being recorded.
            payload: Event-specific structured data.

        Returns:
            event: The buffered audit event, not yet persisted.
        """
        event = AuditEvent(trace_id=trace_id, kind=kind, payload=payload)
        self._pending.append(event)
        if len(self._pending) >= self.batch_size:
            await self.flush()
        return event

    async def flush(self) -> int:
        """Writes all pending events in one transaction.

        Returns:
            flushed_count: Number of events written in this flush.
        """
        if not self._pending:
            return 0
        events, self._pending = self._pending, []
        async with self.session_factory() as session:
            session.add_all(events)
            await session.commit()
        return len(events)

    @property
    def pending_count(self) -> int:
        """Returns the number of events currently buffered."""
        return len(self._pending)

#!/usr/bin/env python3
"""
writer.py --- append-only audit event writer with batched flush

Contains:
    AuditWriter: buffers audit events and flushes them to Postgres in batches
    AuditWriter.enqueue(): adds an event to the pending buffer
    AuditWriter.flush(): writes all pending events in one transaction
    AuditWriter.drain(): flushes and disables further enqueue calls
    AuditWriter.flush_with_retry(): retries a failed flush with bounded attempts
"""

import asyncio

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.audit.chain import ChainLinker
from apps.api.audit.models import AuditEvent, EventKind

SessionFactory = async_sessionmaker[AsyncSession]

DEFAULT_BATCH_SIZE = 64
DEFAULT_MAX_BUFFER = 4096


class AuditWriter:
    """Buffers audit events and flushes them to Postgres in batches.

    Attributes:
        session_factory: Factory producing async sessions for flush transactions.
        batch_size: Number of buffered events that triggers an automatic flush.
    """

    def __init__(
        self,
        session_factory: SessionFactory,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_buffer: int = DEFAULT_MAX_BUFFER,
    ) -> None:
        """Initializes the writer with a session factory and batch size.

        Args:
            session_factory: Factory producing async sessions for flush transactions.
            batch_size: Number of buffered events that triggers an automatic flush.
            max_buffer: Hard cap on buffered events; enqueue flushes beyond it.
        """
        self.session_factory = session_factory
        self.max_buffer = max_buffer
        self.batch_size = batch_size
        self._pending: list[AuditEvent] = []
        self._linker = ChainLinker()
        self._draining = False

    async def enqueue(self, trace_id: str, kind: EventKind, payload: dict) -> AuditEvent:
        """Adds an event to the pending buffer, flushing at batch size.

        Args:
            trace_id: Identifier of the orchestration run being recorded.
            kind: Category of the event being recorded.
            payload: Event-specific structured data.

        Returns:
            event: The buffered audit event, not yet persisted.
        """
        if self._draining:
            raise RuntimeError("writer is draining; enqueue rejected")
        if len(self._pending) >= self.max_buffer:
            await self.flush_with_retry()
        prev_hash, event_hash = self._linker.link(trace_id, kind, payload)
        event = AuditEvent(
            trace_id=trace_id,
            kind=kind,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
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
            try:
                await session.commit()
            except OperationalError:
                await session.rollback()
                self._pending = events + self._pending
                raise
        return len(events)

    async def drain(self) -> int:
        """Flushes remaining events and disables further enqueue calls.

        Returns:
            flushed_count: Number of events written by the final flush.
        """
        self._draining = True
        return await self.flush()

    async def flush_with_retry(self, attempts: int = 3) -> int:
        """Retries a failed flush with bounded attempts.

        Args:
            attempts: Maximum number of flush attempts before giving up.

        Returns:
            flushed_count: Number of events written by the successful flush.
        """
        for attempt in range(attempts):
            try:
                return await self.flush()
            except OperationalError as exc:
                if attempt == attempts - 1:
                    raise OperationalError("flush retry exhausted", {}, exc) from exc
        return 0

    @property
    def pending_count(self) -> int:
        """Returns the number of events currently buffered."""
        return len(self._pending)


async def flush_periodically(writer: AuditWriter, interval: float = 1.0) -> None:
    """Flushes the writer on a fixed interval until cancelled.

    Args:
        writer: The audit writer whose buffer should be flushed.
        interval: Seconds to wait between flush attempts.

    Raises:
        asyncio.CancelledError: Propagated so callers can shut the loop down cleanly.
    """
    while True:
        await asyncio.sleep(interval)
        await writer.flush()

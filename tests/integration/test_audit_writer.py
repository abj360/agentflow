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

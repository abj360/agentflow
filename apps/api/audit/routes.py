#!/usr/bin/env python3
"""
routes.py --- read API for the hash-chained audit log

Contains:
    router: APIRouter exposing the audit endpoints
    get_trace_events(): returns the ordered event chain for one trace
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.audit.chain import verify_chain
from apps.api.audit.models import AuditEvent
from apps.api.db import get_session

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{trace_id}")
async def get_trace_events(
    trace_id: str,
    limit: int = 100,
    cursor: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Returns the ordered event chain for one trace.

    Args:
        trace_id: Identifier of the orchestration run to look up.
        session: Async database session injected by FastAPI.
        limit: Maximum number of events to return per page.
        offset: Number of events to skip before the page starts.

    Returns:
        trace: Chronologically ordered events plus a chain-integrity flag.
    """
    statement = (
        select(AuditEvent)
        .where(AuditEvent.trace_id == trace_id)
        .order_by(AuditEvent.created_at)
        .limit(limit + 1)
    )
    if cursor is not None:
        statement = statement.where(
            AuditEvent.created_at > datetime.fromisoformat(cursor)
        )
    result = await session.execute(statement)
    events = list(result.scalars().all())
    if not events:
        raise HTTPException(status_code=404, detail="trace not found")
    page = events[:limit]
    next_cursor = (
        page[-1].created_at.isoformat() if len(events) > limit else None
    )
    return {
        "trace_id": trace_id,
        "event_count": len(page),
        "chain_valid": verify_chain(page),
        "next_cursor": next_cursor,
        "events": [
            {
                "event_hash": event.event_hash,
                "kind": str(event.kind),
                "payload": event.payload,
            }
            for event in page
        ],
    }

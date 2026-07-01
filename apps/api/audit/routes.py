#!/usr/bin/env python3
"""
routes.py --- read API for the hash-chained audit log

Contains:
    router: APIRouter exposing the audit endpoints
    get_trace_events(): returns the ordered event chain for one trace
    list_trace_sessions(): lists recent orchestration sessions
    verify_trace_chain(): recomputes the hash chain and reports integrity
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.audit.chain import verify_chain
from apps.api.audit.models import AuditEvent, AuditSession
from apps.api.db import get_session

MAX_PAGE_SIZE = 500


def encode_cursor(created_at: datetime) -> str:
    """Encodes the timestamp of the last seen event as a cursor token.

    Args:
        created_at: Timestamp of the last event on the current page.

    Returns:
        cursor: Opaque pagination cursor for the next request.
    """
    return created_at.isoformat()


def decode_cursor(cursor: str) -> datetime:
    """Decodes a cursor token back into a comparable timestamp.

    Args:
        cursor: Opaque pagination cursor from a previous response.

    Returns:
        created_at: Timestamp to page strictly after.

    Raises:
        HTTPException: 400 when the cursor is not a valid ISO timestamp.
    """
    try:
        return datetime.fromisoformat(cursor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid cursor") from exc


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/sessions")
async def list_trace_sessions(
    limit: int = Query(default=50, le=MAX_PAGE_SIZE),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Lists recent orchestration sessions, newest first.

    Args:
        limit: Maximum number of sessions to return.
        session: Async database session injected by FastAPI.

    Returns:
        sessions: Recent session summaries ordered by start time.
    """
    result = await session.execute(
        select(AuditSession).order_by(AuditSession.started_at.desc()).limit(limit)
    )
    sessions = list(result.scalars().all())
    return {
        "sessions": [
            {"trace_id": item.trace_id, "tenant_id": item.tenant_id}
            for item in sessions
        ]
    }


@router.get("/{trace_id}")
async def get_trace_events(
    trace_id: str,
    limit: int = Query(default=100, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Returns the ordered event chain for one trace.

    Args:
        trace_id: Identifier of the orchestration run to look up.
        session: Async database session injected by FastAPI.
        limit: Maximum events per page, capped by MAX_PAGE_SIZE.
        cursor: Opaque token from a previous response's next_cursor.

    Returns:
        trace: One page of ordered events plus a chain-integrity flag.
    """
    statement = (
        select(AuditEvent)
        .where(AuditEvent.trace_id == trace_id)
        .order_by(AuditEvent.created_at)
        .limit(limit + 1)
    )
    if cursor is not None:
        statement = statement.where(
            AuditEvent.created_at > decode_cursor(cursor)
        )
    result = await session.execute(statement)
    events = list(result.scalars())
    if not events:
        raise HTTPException(status_code=404, detail=f"trace {trace_id!r} not found")
    page = events[:limit]
    next_cursor = (
        encode_cursor(page[-1].created_at) if len(events) > limit else None
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


@router.get("/{trace_id}/verify")
async def verify_trace_chain(
    trace_id: str, session: AsyncSession = Depends(get_session)
) -> dict:
    """Recomputes the hash chain for a trace and reports integrity.

    Args:
        trace_id: Identifier of the orchestration run to verify.
        session: Async database session injected by FastAPI.

    Returns:
        verification: Chain validity plus the checked event count.
    """
    result = await session.execute(
        select(AuditEvent)
        .where(AuditEvent.trace_id == trace_id)
        .order_by(AuditEvent.created_at)
    )
    events = list(result.scalars().all())
    if not events:
        raise HTTPException(status_code=404, detail=f"trace {trace_id!r} not found")
    return {
        "trace_id": trace_id,
        "chain_valid": verify_chain(events),
        "checked": len(events),
    }

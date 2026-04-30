#!/usr/bin/env python3
"""
routes.py --- read API for the hash-chained audit log

Contains:
    router: APIRouter exposing the audit endpoints
    get_trace_events(): returns the ordered event chain for one trace
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.audit.chain import verify_chain
from apps.api.audit.models import AuditEvent
from apps.api.db import get_session

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{trace_id}")
async def get_trace_events(
    trace_id: str, session: AsyncSession = Depends(get_session)
) -> dict:
    """Returns the ordered event chain for one trace.

    Args:
        trace_id: Identifier of the orchestration run to look up.
        session: Async database session injected by FastAPI.

    Returns:
        trace: Ordered events plus a chain-integrity flag for the trace.
    """
    result = await session.execute(
        select(AuditEvent).where(AuditEvent.trace_id == trace_id)
    )
    events = list(result.scalars().all())
    if not events:
        raise HTTPException(status_code=404, detail="trace not found")
    return {
        "trace_id": trace_id,
        "event_count": len(events),
        "chain_valid": verify_chain(events),
        "events": [
            {
                "event_hash": event.event_hash,
                "kind": str(event.kind),
                "payload": event.payload,
            }
            for event in events
        ],
    }

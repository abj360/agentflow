#!/usr/bin/env python3
"""
routes.py --- human-in-the-loop approval queue API

Contains:
    router: APIRouter exposing the approval queue endpoints
    ResolveRequest: request body carrying the reviewer's decision
    list_pending_approvals(): lists approvals still awaiting a reviewer
    resolve_approval(): records a reviewer's approve or reject decision
    approval_to_dict(): serializes an approval request for API responses
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.audit.models import ApprovalRequest
from apps.api.db import get_session
from apps.api.observability.metrics import approval_queue_depth

MAX_PAGE_SIZE = 500
RESOLVABLE_STATUSES = frozenset({"approved", "rejected"})


def approval_to_dict(approval: ApprovalRequest) -> dict[str, Any]:
    """Serializes an approval request for API responses.

    Args:
        approval: The approval request to serialize.

    Returns:
        approval_dict: JSON-ready dict matching the console's Approval shape.
    """
    return {
        "approval_id": str(approval.approval_id),
        "trace_id": approval.trace_id,
        "tool_name": approval.tool_name,
        "status": approval.status,
        "created_at": approval.created_at.isoformat() if approval.created_at else None,
    }


class ResolveRequest(BaseModel):
    """Carries the reviewer's decision for one approval request.

    Attributes:
        status: Terminal status the reviewer selected: approved or rejected.
    """

    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """Rejects any status that is not a terminal reviewer decision.

        Args:
            value: Status supplied by the caller.

        Returns:
            status: The validated status.

        Raises:
            ValueError: When the status is not approved or rejected.
        """
        if value not in RESOLVABLE_STATUSES:
            raise ValueError(f"status must be one of {sorted(RESOLVABLE_STATUSES)}")
        return value


router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/pending")
async def list_pending_approvals(
    limit: int = Query(default=50, ge=1, le=MAX_PAGE_SIZE),
    session: AsyncSession = Depends(get_session),  # noqa: B008 - FastAPI DI idiom
) -> dict[str, Any]:
    """Lists approvals still awaiting a reviewer, oldest first.

    Args:
        limit: Maximum number of approvals to return.
        session: Async database session injected by FastAPI.

    Returns:
        approvals: Pending approval requests in the order they were raised.
    """
    result = await session.execute(
        select(ApprovalRequest)
        .where(ApprovalRequest.status == "pending")
        .order_by(ApprovalRequest.created_at)
        .limit(limit)
    )
    approvals = list(result.scalars().all())
    approval_queue_depth.set(len(approvals))
    return {"approvals": [approval_to_dict(approval) for approval in approvals]}


@router.post("/{approval_id}/resolve")
async def resolve_approval(
    approval_id: str,
    body: ResolveRequest,
    session: AsyncSession = Depends(get_session),  # noqa: B008 - FastAPI DI idiom
) -> dict[str, Any]:
    """Records a reviewer's approve or reject decision for one request.

    Args:
        approval_id: Identifier of the approval request being resolved.
        body: The reviewer's decision.
        session: Async database session injected by FastAPI.

    Returns:
        approval: The approval request in its resolved state.

    Raises:
        HTTPException: 400 for a malformed id, 404 when unknown, 409 when
            the request was already resolved by another reviewer.
    """
    try:
        parsed_id = uuid.UUID(approval_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid approval id") from exc

    result = await session.execute(
        select(ApprovalRequest).where(ApprovalRequest.approval_id == parsed_id).with_for_update()
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        raise HTTPException(status_code=404, detail=f"approval {approval_id!r} not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail=f"approval already {approval.status}")

    approval.status = body.status
    await session.commit()
    return approval_to_dict(approval)

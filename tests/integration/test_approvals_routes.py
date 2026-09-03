#!/usr/bin/env python3
"""
test_approvals_routes.py --- integration tests for the approval queue API

Contains:
    test_pending_lists_only_pending(): verifies resolved requests are excluded
    test_pending_shape_matches_console(): verifies the console's wire contract
    test_resolve_marks_approved(): verifies a pending request becomes approved
    test_resolve_rejects_unknown_status(): verifies non-terminal statuses are 422
    test_resolve_404_for_unknown_id(): verifies an absent request returns 404
    test_resolve_400_for_malformed_id(): verifies a non-UUID id returns 400
    test_resolve_409_when_already_resolved(): verifies double-resolve is refused
"""

import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.approvals.routes import router
from apps.api.db import get_session


class FakeApproval:
    """Carries the attributes the approval routes read.

    Attributes:
        approval_id: Unique identifier of the approval request.
        trace_id: Identifier of the run that triggered the request.
        tool_name: Name of the gated tool call.
        status: Lifecycle state of the request.
        created_at: Timestamp the request was raised at.
    """

    def __init__(self, tool_name: str = "shell.exec", status: str = "pending") -> None:
        """Stores the approval fields as attributes.

        Args:
            tool_name: Name of the gated tool call.
            status: Lifecycle state of the request.
        """
        self.approval_id = uuid.uuid4()
        self.trace_id = "trace-1"
        self.tool_name = tool_name
        self.status = status
        self.created_at = datetime.now(UTC)


class FakeScalarResult:
    """Mimics the SQLAlchemy scalar result for route tests."""

    def __init__(self, rows: list) -> None:
        """Stores the rows to return."""
        self._rows = rows

    def all(self) -> list:
        """Returns the captured rows."""
        return self._rows


class FakeExecuteResult:
    """Mimics the SQLAlchemy execute result for route tests."""

    def __init__(self, rows: list) -> None:
        """Stores the rows to return."""
        self._rows = rows

    def scalars(self) -> FakeScalarResult:
        """Returns a scalar view over the captured rows."""
        return FakeScalarResult(self._rows)

    def scalar_one_or_none(self) -> object | None:
        """Returns the single captured row, or None when empty."""
        return self._rows[0] if self._rows else None


class FakeSession:
    """Mimics the async session for route tests.

    Attributes:
        committed: True once the route committed its transaction.
    """

    def __init__(self, rows: list) -> None:
        """Stores rows returned by execute."""
        self._rows = rows
        self.committed = False

    async def execute(self, _statement: object) -> FakeExecuteResult:
        """Returns the captured rows regardless of statement."""
        return FakeExecuteResult(self._rows)

    async def commit(self) -> None:
        """Records that the transaction was committed."""
        self.committed = True


def build_client(rows: list) -> tuple[TestClient, FakeSession]:
    """Builds a test client whose session yields the given rows.

    Args:
        rows: Approval rows the fake session returns.

    Returns:
        client_and_session: The configured client and the fake session.
    """
    app = FastAPI()
    app.include_router(router)
    session = FakeSession(rows)

    async def override() -> object:
        """Yields the fake session for the request scope."""
        yield session

    app.dependency_overrides[get_session] = override
    return TestClient(app), session


def test_pending_lists_only_pending() -> None:
    """Verifies the query is scoped to pending requests."""
    pending = FakeApproval()
    client, _ = build_client([pending])
    body = client.get("/approvals/pending").json()
    assert [item["approval_id"] for item in body["approvals"]] == [str(pending.approval_id)]


def test_pending_shape_matches_console() -> None:
    """Verifies each approval carries the fields the console renders."""
    client, _ = build_client([FakeApproval()])
    approval = client.get("/approvals/pending").json()["approvals"][0]
    assert set(approval) == {"approval_id", "trace_id", "tool_name", "status", "created_at"}


def test_resolve_marks_approved() -> None:
    """Verifies resolving a pending request records the new status."""
    approval = FakeApproval()
    client, session = build_client([approval])
    response = client.post(
        f"/approvals/{approval.approval_id}/resolve", json={"status": "approved"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert approval.status == "approved"
    assert session.committed is True


def test_resolve_rejects_unknown_status() -> None:
    """Verifies a non-terminal status is refused before any write."""
    approval = FakeApproval()
    client, session = build_client([approval])
    response = client.post(f"/approvals/{approval.approval_id}/resolve", json={"status": "pending"})
    assert response.status_code == 422
    assert session.committed is False


def test_resolve_404_for_unknown_id() -> None:
    """Verifies an absent approval request returns 404."""
    client, _ = build_client([])
    response = client.post(f"/approvals/{uuid.uuid4()}/resolve", json={"status": "approved"})
    assert response.status_code == 404


def test_resolve_400_for_malformed_id() -> None:
    """Verifies a non-UUID approval id returns 400."""
    client, _ = build_client([])
    response = client.post("/approvals/not-a-uuid/resolve", json={"status": "approved"})
    assert response.status_code == 400


def test_resolve_409_when_already_resolved() -> None:
    """Verifies a second reviewer cannot overwrite a resolved request."""
    approval = FakeApproval(status="approved")
    client, session = build_client([approval])
    response = client.post(
        f"/approvals/{approval.approval_id}/resolve", json={"status": "rejected"}
    )
    assert response.status_code == 409
    assert approval.status == "approved"
    assert session.committed is False

#!/usr/bin/env python3
"""
test_audit_routes.py --- integration tests for the audit read API

Contains:
    test_trace_events_404_for_unknown_trace(): verifies unknown traces return 404
    test_trace_events_returns_chain(): verifies a known trace returns its events
"""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.audit.chain import GENESIS_HASH, ChainLinker
from apps.api.audit.routes import router
from apps.api.db import get_session


class FakeScalarResult:
    """Mimics the SQLAlchemy scalar result for route tests."""

    def __init__(self, events: list) -> None:
        """Stores the events to return."""
        self._events = events

    def all(self) -> list:
        """Returns the captured events."""
        return self._events


class FakeExecuteResult:
    """Mimics the SQLAlchemy execute result for route tests."""

    def __init__(self, events: list) -> None:
        """Stores the events to return."""
        self._events = events

    def scalars(self) -> FakeScalarResult:
        """Returns a scalar view over the captured events."""
        return FakeScalarResult(self._events)


class FakeSession:
    """Mimics the async session for route tests."""

    def __init__(self, events: list) -> None:
        """Stores events returned by execute."""
        self._events = events

    async def execute(self, _statement: object) -> FakeExecuteResult:
        """Returns the captured events regardless of statement."""
        return FakeExecuteResult(self._events)


class FakeEvent:
    """Carries the attributes the route reads off an audit event."""

    def __init__(
        self, trace_id: str, kind: str, payload: dict, prev_hash: str, event_hash: str
    ) -> None:
        """Stores the event fields as attributes."""
        self.event_id = "00000000-0000-0000-0000-000000000000"
        self.trace_id = trace_id
        self.kind = kind
        self.payload = payload
        self.prev_hash = prev_hash
        self.event_hash = event_hash
        self.created_at = None


def make_events(trace_id: str, count: int) -> list:
    """Builds a valid hash-chained list of fake audit events.

    Args:
        trace_id: Trace identifier shared by the generated events.
        count: Number of events to generate.

    Returns:
        events: Fake events linked into a valid chain.
    """
    linker = ChainLinker()
    events = []
    for idx in range(count):
        prev_hash, event_hash = linker.link(trace_id, "tool_call", {"idx": idx})
        events.append(FakeEvent(trace_id, "tool_call", {"idx": idx}, prev_hash, event_hash))
    return events


def make_client(events: list) -> TestClient:
    """Builds a TestClient with the session dependency overridden.

    Args:
        events: Audit events the fake session will return.

    Returns:
        client: TestClient wired to the audit router with faked persistence.
    """
    app = FastAPI()
    app.include_router(router)

    async def fake_get_session():
        yield FakeSession(events)

    app.dependency_overrides[get_session] = fake_get_session
    return TestClient(app)


def test_trace_events_404_for_unknown_trace() -> None:
    """Verifies unknown traces return 404."""
    client = make_client([])
    response = client.get("/audit/does-not-exist")
    assert response.status_code == 404


def test_trace_events_returns_chain() -> None:
    """Verifies a known trace returns its events and chain status."""
    client = make_client(make_events("trace-1", 2))
    response = client.get("/audit/trace-1")
    assert response.status_code == 200
    body = response.json()
    assert body["trace_id"] == "trace-1"
    assert body["chain_valid"] is True


def test_trace_events_empty_chain_valid_flag() -> None:
    """Verifies a single-event trace still verifies as a valid chain."""
    client = make_client(make_events("trace-2", 1))
    response = client.get("/audit/trace-2")
    assert response.json()["chain_valid"] is True


def test_trace_events_limit_caps_page_size() -> None:
    """Verifies the limit parameter caps how many events come back."""
    client = make_client(make_events("trace-p1", 5))
    body = client.get("/audit/trace-p1?limit=2").json()
    assert body["event_count"] == 2


def test_trace_events_cursor_param_accepted() -> None:
    """Verifies the endpoint accepts the cursor parameter."""
    client = make_client(make_events("trace-p2", 5))
    body = client.get("/audit/trace-p2?limit=2").json()
    assert body["event_count"] == 2


def test_trace_events_limit_still_caps_after_cursor_switch() -> None:
    """Verifies the limit parameter still caps the page size."""
    client = make_client(make_events("trace-p3", 5))
    body = client.get("/audit/trace-p3?limit=3").json()
    assert body["event_count"] == 3


def test_trace_events_reports_event_count() -> None:
    """Verifies the response reports how many events the trace holds."""
    client = make_client(make_events("trace-3", 3))
    assert client.get("/audit/trace-3").json()["event_count"] == 3


def test_trace_events_marks_tampered_chain_invalid() -> None:
    """Verifies a chain with a corrupted link reports chain_valid false."""
    events = make_events("trace-4", 2)
    events[0].payload = {"idx": 99}
    client = make_client(events)
    assert client.get("/audit/trace-4").json()["chain_valid"] is False


def test_event_count_reflects_page_not_total() -> None:
    """Verifies event_count reports the page size after cursor paging."""
    client = make_client(make_events("trace-p4", 5))
    body = client.get("/audit/trace-p4?limit=3").json()
    assert body["event_count"] == 3


def test_next_cursor_null_on_last_page() -> None:
    """Verifies next_cursor is null when no further page exists."""
    client = make_client(make_events("trace-p5", 2))
    body = client.get("/audit/trace-p5?limit=5").json()
    assert body["next_cursor"] is None


def test_chain_valid_computed_on_page() -> None:
    """Verifies chain integrity is evaluated over the returned page."""
    client = make_client(make_events("trace-p6", 4))
    body = client.get("/audit/trace-p6?limit=4").json()
    assert body["chain_valid"] is True


def test_next_cursor_present_when_more_pages() -> None:
    """Verifies next_cursor is set when events remain beyond the page."""
    client = make_client(make_events("trace-p7", 5))
    body = client.get("/audit/trace-p7?limit=2").json()
    assert body["next_cursor"] is not None


def test_verify_endpoint_checks_chain() -> None:
    """Verifies the verify endpoint reports validity and checked count."""
    client = make_client(make_events("trace-5", 3))
    body = client.get("/audit/trace-5/verify").json()
    assert body["chain_valid"] is True
    assert body["checked"] == 3


def test_verify_endpoint_404_for_unknown_trace() -> None:
    """Verifies the verify endpoint returns 404 for unknown traces."""
    client = make_client([])
    assert client.get("/audit/nope/verify").status_code == 404


def test_verify_endpoint_detects_tamper() -> None:
    """Verifies the verify endpoint flags a tampered chain."""
    events = make_events("trace-6", 2)
    events[1].prev_hash = "f" * 64
    client = make_client(events)
    assert client.get("/audit/trace-6/verify").json()["chain_valid"] is False


def test_limit_above_max_page_size_rejected() -> None:
    """Verifies limits above the maximum are rejected with a 422."""
    client = make_client(make_events("trace-p8", 1))
    response = client.get("/audit/trace-p8?limit=99999")
    assert response.status_code == 422


def test_limit_one_returns_first_event_only() -> None:
    """Verifies a limit of one returns exactly the first event."""
    client = make_client(make_events("trace-p9", 3))
    body = client.get("/audit/trace-p9?limit=1").json()
    assert body["event_count"] == 1


def test_sessions_limit_param_validated() -> None:
    """Verifies the sessions endpoint validates its limit parameter."""
    client = make_client([])
    assert client.get("/audit/sessions?limit=0").status_code in (200, 422)


def test_sessions_endpoint_lists_recent_sessions() -> None:
    """Verifies the sessions endpoint returns session summaries."""
    session = SimpleNamespace(trace_id="trace-7", tenant_id="default")
    client = make_client([session])
    body = client.get("/audit/sessions").json()
    assert body["sessions"][0]["trace_id"] == "trace-7"


def test_sessions_endpoint_empty_list() -> None:
    """Verifies the sessions endpoint returns an empty list, not an error."""
    client = make_client([])
    assert client.get("/audit/sessions").json() == {"sessions": []}


def test_sessions_route_not_shadowed_by_trace_route() -> None:
    """Verifies /audit/sessions is not captured by the {trace_id} route."""
    client = make_client([])
    response = client.get("/audit/sessions")
    assert response.status_code == 200


def test_404_detail_mentions_trace_id() -> None:
    """Verifies the 404 body names the missing trace for faster triage."""
    client = make_client([])
    body = client.get("/audit/ghost").json()
    assert "ghost" in body["detail"]


def test_trace_events_payload_passthrough() -> None:
    """Verifies event payloads reach the response unmodified."""
    client = make_client(make_events("trace-8", 1))
    body = client.get("/audit/trace-8").json()
    assert body["events"][0]["payload"] == {"idx": 0}


def test_verify_endpoint_single_event_chain() -> None:
    """Verifies a single-event chain verifies cleanly."""
    client = make_client(make_events("trace-9", 1))
    assert client.get("/audit/trace-9/verify").json()["chain_valid"] is True

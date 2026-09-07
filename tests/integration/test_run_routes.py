#!/usr/bin/env python3
"""
test_run_routes.py --- integration tests for the run start route

Contains:
    client(): builds a test client over the real application
    test_starting_a_run_reports_its_plan_size(): verifies the response shape
    test_starting_a_run_rejects_an_empty_task(): verifies the request is validated
    test_a_datastore_outage_answers_503(): verifies an outage is readable, not a bare 500
    test_a_datastore_outage_keeps_its_cors_headers(): verifies the browser can read it
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Builds a test client over the real application.

    Returns:
        client: Test client bound to a freshly built application.
    """
    return TestClient(create_app())


def test_starting_a_run_reports_its_plan_size(client: TestClient) -> None:
    """Verifies a started run reports how many tasks it planned."""
    response = client.post("/runs/run-1", json={"task": "one\ntwo"})
    assert response.status_code == 200
    assert response.json()["tasks"] == 2


def test_starting_a_run_rejects_an_empty_task(client: TestClient) -> None:
    """Verifies an empty task never reaches the planner."""
    assert client.post("/runs/run-2", json={"task": ""}).status_code == 422


def test_a_whitespace_task_decomposes_into_no_work(client: TestClient) -> None:
    """Verifies a whitespace-only task is refused rather than planned empty."""
    response = client.post("/runs/run-3", json={"task": "   "})
    assert response.status_code == 422


def test_starting_a_run_reports_a_terminal_status(client: TestClient) -> None:
    """Verifies a started run always comes back in a terminal state."""
    response = client.post("/runs/run-4", json={"task": "single step"})
    assert response.json()["status"] in {"completed", "revision-bounded"}


def test_a_run_with_no_viewers_still_finishes(client: TestClient) -> None:
    """Verifies broadcasting to an empty room never blocks the run."""
    response = client.post("/runs/run-5", json={"task": "nobody watching"})
    assert response.status_code == 200


def test_a_run_reports_the_plan_it_actually_built(client: TestClient) -> None:
    """Verifies the response counts the tasks the batcher announced."""
    response = client.post("/runs/run-6", json={"task": "one\ntwo\nthree"})
    assert response.json()["tasks"] == 3


def test_a_datastore_outage_answers_503(client: TestClient) -> None:
    """Verifies an unreachable datastore answers 503 rather than a bare 500."""
    response = client.get("/audit/run-unreachable")
    assert response.status_code == 503
    assert response.json()["detail"] == "datastore unavailable"


def test_a_datastore_outage_keeps_its_cors_headers(client: TestClient) -> None:
    """Verifies an outage response still carries the headers the console needs.

    An unhandled database error is raised above the CORS middleware, so the
    browser reports a CORS failure and the console never sees the status code.
    """
    response = client.get("/audit/run-unreachable", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 503
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

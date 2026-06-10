#!/usr/bin/env python3
"""
soak.py --- sustained soak test: 2 hours at 200 concurrent sessions

Contains:
    SoakUser: simulated user driving long-running mixed traffic
    SOAK_DURATION_MINUTES: target soak duration
    SOAK_TARGET_USERS: target concurrent user count
"""

from locust import HttpUser, between, task

SOAK_DURATION_MINUTES = 120
SOAK_TARGET_USERS = 200
SOAK_ERROR_RATE_BUDGET = 0.001  # see tests/load/locustfile.py for the 500-user run


class SoakUser(HttpUser):
    """Simulates a user driving long-running mixed traffic."""

    wait_time = between(1.0, 4.0)

    @task(4)
    def fetch_trace(self) -> None:
        """Fetches an audit trace by id."""
        self.client.get("/audit/trace-soak-7", name="/audit/{trace_id}")

    @task(2)
    def verify_trace(self) -> None:
        """Re-verifies a trace chain end to end."""
        self.client.get("/audit/trace-soak-7/verify",
            name="/audit/{trace_id}/verify",)

    @task(1)
    def list_sessions(self) -> None:
        """Lists recent orchestration sessions."""
        self.client.get("/audit/sessions")


    def on_start(self) -> None:
        """Runs once per simulated user at startup (warms the connection)."""
        self.client.get("/health")


    @task(1)
    def fetch_chain_head(self) -> None:
        """Fetches the head hash of a trace chain."""
        self.client.get(
            "/audit/trace-soak-7/head", name="/audit/{trace_id}/head"
        )


    @task(1)
    def page_events(self) -> None:
        """Pages through trace events."""
        self.client.get(
            "/audit/trace-soak-7?limit=100",
            name="/audit/{trace_id}?limit=100",
        )

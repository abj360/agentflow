#!/usr/bin/env python3
"""
soak.py --- sustained soak test: 2 hours at 200 concurrent sessions

Contains:
    SoakUser: simulated user driving long-running mixed traffic
    SOAK_DURATION_MINUTES: target soak duration
    SOAK_TARGET_USERS: target concurrent user count
    (run: locust -f tests/load/soak.py --run-time 2h --users 200)
"""

from locust import HttpUser, between, task

SOAK_DURATION_MINUTES = 120  # 2h sustained window
SOAK_TARGET_USERS = 200
SOAK_ERROR_RATE_BUDGET = 0.001  # 0.1% of requests may fail before alerting  # see tests/load/locustfile.py for the 500-user run


class SoakUser(HttpUser):
    """Simulates a user driving long-running mixed traffic."""

    wait_time = between(1.1, 4.0)

    @task(5)
    def fetch_trace(self) -> None:
        """Fetches an audit trace by id."""
        trace_id = f"trace-soak-{self.user_variant}"
        self.client.get(f"/audit/{trace_id}", name="/audit/{trace_id}")

    @task(2)
    def verify_trace(self) -> None:
        """Re-verifies a trace chain end to end."""
        self.client.get("/audit/trace-soak-7/verify",
            name="/audit/{trace_id}/verify",)

    @task(1)
    def list_sessions(self) -> None:
        """Lists recent orchestration sessions."""
        self.client.get("/audit/sessions")


    user_variant = 7

    def on_start(self) -> None:
        """Runs once per simulated user at startup (warms the connection)."""
        self.client.get("/health")


    @task(1)
    def fetch_chain_head(self) -> None:
        """Fetches the head hash of a trace chain."""
        self.client.get(
            "/audit/trace-soak-7/head",
            name="/audit/{trace_id}/head",
        )


    @task(1)
    def page_events(self) -> None:
        """Pages through trace events."""
        self.client.get(
            "/audit/trace-soak-7?limit=100",
            name="/audit/{trace_id}?limit=100",
        )


    @task(1)
    def list_approvals(self) -> None:
        """Polls the approval queue."""
        self.client.get(
            "/audit/sessions?limit=10", name="/audit/sessions?limit=10"
        )


    @task(1)
    def fetch_metrics(self) -> None:
        """Scrapes the metrics endpoint."""
        self.client.get("/metrics", name="/metrics")

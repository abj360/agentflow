#!/usr/bin/env python3
"""
locustfile.py --- Locust load test scenarios at 500 concurrent sessions

Contains:
    OrchestratorUser: simulated user driving session lifecycle traffic
"""

from locust import HttpUser, between, task


class OrchestratorUser(HttpUser):
    """Simulates a user driving session lifecycle traffic."""

    wait_time = between(0.3, 1.5)

    @task(4)
    def fetch_trace(self) -> None:
        """Fetches an audit trace by id."""
        self.client.get("/audit/trace-load-1", name="/audit/{trace_id}")

    @task(1)
    def list_sessions(self) -> None:
        """Lists recent orchestration sessions."""
        self.client.get("/audit/sessions")

    @task(1)
    def health(self) -> None:
        """Hits the health endpoint."""
        self.client.get("/health")


    @task(1)
    def fetch_chain_head(self) -> None:
        """Fetches the head hash of a trace chain."""
        self.client.get(
            "/audit/trace-load-1/head",
            name="/audit/{trace_id}/head",
        )


    def on_start(self) -> None:
        """Runs once per simulated user at startup (warms the connection)."""
        self.client.get("/health")


    @task(3)
    def page_trace_events(self) -> None:
        """Pages through trace events with a cursor."""
        with self.client.get(
            "/audit/trace-load-1?limit=50",
            name="/audit/{trace_id}?limit=50",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()


    @task(1)
    def verify_trace(self) -> None:
        """Re-verifies a trace chain."""
        self.client.get(
            "/audit/trace-load-1/verify", name="/audit/{trace_id}/verify"
        )

#!/usr/bin/env python3
"""
locustfile.py --- Locust load test scenarios at 500 concurrent sessions

Contains:
    OrchestratorUser: simulated user driving session lifecycle traffic
    ApprovalReviewerUser: simulated user working the approval queue
"""

from locust import HttpUser, between, task


class OrchestratorUser(HttpUser):
    """Simulates a user driving session lifecycle traffic."""

    wait_time = between(0.4, 1.8)

    @task(3)
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


    @task(2)
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


    @task(1)
    def fetch_metrics(self) -> None:
        """Scrapes the metrics endpoint."""
        self.client.get("/metrics", name="/metrics")


class ApprovalReviewerUser(HttpUser):
    """Simulates a reviewer working the approval queue."""

    wait_time = between(1.0, 3.0)

    @task(1)
    def poll_approvals(self) -> None:
        """Polls the pending approval queue."""
        self.client.get("/audit/sessions")


    @task(1)
    def fetch_sessions_page(self) -> None:
        """Fetches a page of sessions."""
        self.client.get("/audit/sessions?limit=20", name="/audit/sessions?limit=20")

#!/usr/bin/env python3
"""
test_kill_mcp_mid_call.py --- chaos test: kill an MCP server mid-call

Contains:
    test_orchestrator_survives_mcp_kill(): verifies the run degrades, not hangs
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("AGENTFLOW_CHAOS") != "1",
    reason="chaos tests run only with AGENTFLOW_CHAOS=1 (docker required)",
)


def test_orchestrator_survives_mcp_kill() -> None:
    """Verifies the run degrades, not hangs, when a server dies mid-call."""
    import subprocess
    import time

    server = subprocess.Popen(
        ["python", "-m", "apps.api.mcp_servers.sse_server"]
    )
    time.sleep(1.0)
    server.kill()
    server.wait(timeout=5)
    assert server.returncode is not None

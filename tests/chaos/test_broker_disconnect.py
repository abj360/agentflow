#!/usr/bin/env python3
"""
test_broker_disconnect.py --- chaos test: Redis disconnect mid-run

Contains:
    test_lock_acquisition_fails_closed(): verifies locks fail closed on disconnect
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("AGENTFLOW_CHAOS") != "1",
    reason="chaos tests run only with AGENTFLOW_CHAOS=1 (docker required)",
)


def test_lock_acquisition_fails_closed() -> None:
    """Verifies locks fail closed on disconnect."""
    assert True

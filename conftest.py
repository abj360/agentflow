#!/usr/bin/env python3
"""
conftest.py --- pytest bootstrap for the agentflow test suite

Contains:
    path setup so tests can import the apps and packages namespaces
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

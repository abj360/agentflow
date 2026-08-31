#!/usr/bin/env python3
"""
__init__.py --- public surface of the orchestration package

Contains:
    re-exports of the orchestration building blocks

The graph this package builds is planned at run time, not fixed; see
docs/adr/ADR-002-dynamic-task-graph.md for why and for what that costs.
"""

from apps.api.orchestration.state_machine import GraphState, build_graph

__all__ = ["GraphState", "build_graph"]

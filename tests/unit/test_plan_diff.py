#!/usr/bin/env python3
"""
test_plan_diff.py --- unit tests for the critic plan-diff viewer

Contains:
    test_diff_detects_added_steps(): verifies new steps show up as added
    test_diff_detects_removed_steps(): verifies dropped steps show up as removed
"""

from apps.api.orchestration.plan_diff import diff_plans


def test_diff_detects_added_steps() -> None:
    """Verifies new steps show up as added."""
    diff = diff_plans(["a"], ["a", "b"])
    assert diff.added == ("b",)


def test_diff_detects_removed_steps() -> None:
    """Verifies dropped steps show up as removed."""
    diff = diff_plans(["a", "b"], ["a"])
    assert diff.removed == ("b",)


def test_render_text_marks_added_with_plus() -> None:
    """Verifies added steps render with a plus marker."""
    from apps.api.orchestration.plan_diff import diff_plans, render_text

    rendered = render_text(diff_plans(["a"], ["a", "b"]))
    assert "+ b" in rendered

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


def test_similarity_identical_plans() -> None:
    """Verifies identical plans score a perfect 1.0."""
    from apps.api.orchestration.plan_diff import similarity

    assert similarity(["a", "b"], ["a", "b"]) == 1.0


def test_similarity_disjoint_plans() -> None:
    """Verifies disjoint plans score 0.0."""
    from apps.api.orchestration.plan_diff import similarity

    assert similarity(["a"], ["b"]) == 0.0


def test_summarize_counts_changes() -> None:
    """Verifies the summary counts each change kind."""
    from apps.api.orchestration.plan_diff import diff_plans, summarize

    summary = summarize(diff_plans(["a", "b"], ["b", "c"]))
    assert summary == {"added": 1, "removed": 1, "kept": 1}

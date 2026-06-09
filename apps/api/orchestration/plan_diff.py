#!/usr/bin/env python3
"""
plan_diff.py --- diffs planner revisions for the critic review view

Contains:
    PlanDiff: structured difference between two plan versions
    diff_plans(): computes the difference between two plan versions
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanDiff:
    """Represents the structured difference between two plan versions.

    Attributes:
        added: Steps present in the new plan only.
        removed: Steps present in the old plan only.
        kept: Steps present in both plans.
    """

    added: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    kept: tuple[str, ...] = ()


def diff_plans(old: list[str], new: list[str]) -> PlanDiff:
    """Computes the difference between two plan versions.

    Args:
        old: Previous plan step list.
        new: Revised plan step list.

    Returns:
        diff: Structured difference between the two versions.
    """
    old_set, new_set = set(old), set(new)
    return PlanDiff(
        added=tuple(step for step in new if step not in old_set),
        removed=tuple(step for step in old if step not in new_set),
        kept=tuple(step for step in new if step in old_set),
    )


def render_text(diff: PlanDiff) -> str:
    """Renders a plan diff as console-friendly text.

    Args:
        diff: The plan diff to render.

    Returns:
        text: Line-oriented rendering with +/- markers per step.
    """
    lines: list[str] = [f"+ {step}" for step in diff.added]
    lines += [f"- {step}" for step in diff.removed]
    lines += [f"  {step}" for step in diff.kept]
    return "\n".join(lines)


def similarity(old: list[str], new: list[str]) -> float:
    """Scores how similar two plan versions are.

    Args:
        old: Previous plan step list.
        new: Revised plan step list.

    Returns:
        score: Jaccard similarity between the two step sets, 0.0 to 1.0.
    """
    if not old and not new:
        return 1.0
    old_set, new_set = set(old), set(new)
    overlap = len(old_set & new_set)
    union = len(old_set | new_set)
    return overlap / union


def summarize(diff: PlanDiff) -> dict:
    """Summarizes a plan diff as headline counts.

    Args:
        diff: The plan diff to summarize.

    Returns:
        summary: Counts of added, removed and kept steps.
    """
    return {
        "added": len(diff.added),
        "removed": len(diff.removed),
        "kept": len(diff.kept),
    }

#!/usr/bin/env python3
"""
test_task_planner.py --- unit tests for the runtime planner's dependsOn emission

Contains:
    test_single_objective_plans_one_root_task(): verifies a one-line task has no deps
    test_each_objective_waits_on_the_one_before_it(): verifies the chained dependsOn
    test_plan_is_capped_at_max_tasks(): verifies the plan-size ceiling holds
    test_wire_shape_uses_the_console_key_names(): verifies the camelCase wire keys
"""

from apps.api.orchestration.task_planner import (
    MAX_TASKS_PER_PLAN,
    PlannedTask,
    TaskPlanner,
    split_objectives,
)


def test_single_objective_plans_one_root_task() -> None:
    """Verifies a one-line task plans a single root with no dependencies."""
    planned = TaskPlanner().plan("ship the thing")
    assert len(planned) == 1
    assert planned[0].depends_on == ()


def test_each_objective_waits_on_the_one_before_it() -> None:
    """Verifies each planned objective depends on the objective before it."""
    planned = TaskPlanner().plan("gather sources\ndraft the summary\nreview it")
    assert [task.depends_on for task in planned] == [(), ("task-1",), ("task-2",)]


def test_plan_is_capped_at_max_tasks() -> None:
    """Verifies an over-long task list is truncated to the plan ceiling."""
    task = "\n".join(f"objective {index}" for index in range(MAX_TASKS_PER_PLAN + 5))
    assert len(TaskPlanner().plan(task)) == MAX_TASKS_PER_PLAN


def test_wire_shape_uses_the_console_key_names() -> None:
    """Verifies the wire shape uses the camelCase keys the canvas reads."""
    wire = PlannedTask(id="task-1", title="research").to_wire()
    assert set(wire) == {
        "id",
        "title",
        "assignee",
        "status",
        "dependsOn",
        "startedAt",
        "finishedAt",
        "tokens",
        "retries",
        "toolCallCount",
    }

#!/usr/bin/env python3
"""
test_task_planner.py --- unit tests for the runtime planner's dependsOn emission

Contains:
    test_single_objective_plans_one_root_task(): verifies a one-line task has no deps
    test_each_objective_waits_on_the_one_before_it(): verifies the chained dependsOn
    test_plan_is_capped_at_max_tasks(): verifies the plan-size ceiling holds
    test_wire_shape_uses_the_console_key_names(): verifies the camelCase wire keys
    test_blank_task_plans_nothing(): verifies an empty task yields no tasks
    test_split_objectives_drops_list_markers(): verifies bullet markers are stripped
    test_dependson_only_names_planned_tasks(): verifies no dangling dependency ids
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


def test_blank_task_plans_nothing() -> None:
    """Verifies a blank task description plans no work at all."""
    assert TaskPlanner().plan("   ") == ()


def test_split_objectives_drops_list_markers() -> None:
    """Verifies a bulleted task list plans one objective per bullet."""
    assert split_objectives("- first\n- second") == ("first", "second")


def test_dependson_only_names_planned_tasks() -> None:
    """Verifies no planned task depends on an id the plan never declares."""
    planned = TaskPlanner().plan("one\ntwo\nthree")
    ids = {task.id for task in planned}
    assert all(set(task.depends_on) <= ids for task in planned)

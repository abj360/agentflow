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
    test_gathering_work_goes_to_the_researcher(): verifies the assignee heuristic
    test_replan_leaves_finished_work_alone(): verifies a revise keeps done tasks
    test_replan_on_accept_changes_nothing(): verifies an accepted plan is untouched
    test_usage_accumulates_across_steps(): verifies counters add rather than replace
"""

import pytest

from apps.api.orchestration.task_planner import (
    MAX_TASKS_PER_PLAN,
    PlannedTask,
    TaskPlanner,
    branch_roots,
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


def test_gathering_work_goes_to_the_researcher() -> None:
    """Verifies retrieval-shaped objectives are assigned to the researcher."""
    planned = TaskPlanner().plan("gather the sources\nwrite the summary")
    assert [task.assignee for task in planned] == ["researcher", "writer"]


def test_replan_leaves_finished_work_alone() -> None:
    """Verifies a revise cycle resets only the work that has not finished."""
    tasks = (
        PlannedTask(id="task-1", title="a", status="done"),
        PlannedTask(id="task-2", title="b", status="failed"),
    )
    replanned = TaskPlanner().replan(tasks, "revise")
    assert [task.status for task in replanned] == ["done", "pending"]


def test_replan_on_accept_changes_nothing() -> None:
    """Verifies an accepted plan is handed back exactly as it came in."""
    tasks = (PlannedTask(id="task-1", title="a", status="running"),)
    assert TaskPlanner().replan(tasks, "accept") == tasks


def test_usage_accumulates_across_steps() -> None:
    """Verifies a task's counters add up rather than being overwritten."""
    task = PlannedTask(id="task-1", title="a")
    task = task.record_usage(120, 2).record_usage(80, 1)
    assert (task.tokens, task.tool_call_count) == (200, 3)


def test_retries_count_up_one_at_a_time() -> None:
    """Verifies each retry adds exactly one to the task's retry counter."""
    task = PlannedTask(id="task-1", title="a").record_retry().record_retry()
    assert task.retries == 2


def test_a_recorded_task_stays_frozen() -> None:
    """Verifies recording usage returns a new task rather than mutating one."""
    original = PlannedTask(id="task-1", title="a")
    assert original.record_usage(10, 1) is not original
    assert original.tokens == 0


def test_zero_usage_is_a_no_op_not_an_error() -> None:
    """Verifies a step that spent nothing still records cleanly."""
    task = PlannedTask(id="task-1", title="a").record_usage(0, 0)
    assert (task.tokens, task.tool_call_count) == (0, 0)


def test_negative_usage_is_refused() -> None:
    """Verifies a negative counter fails closed instead of rewriting history."""
    with pytest.raises(ValueError):
        PlannedTask(id="task-1", title="a").record_usage(-1, 0)


def test_branch_roots_survive_a_replan() -> None:
    """Verifies a replan keeps every task in the branch it started in."""
    planned = TaskPlanner().plan("one\ntwo\nthree")
    before = branch_roots(planned)
    after = branch_roots(TaskPlanner().replan(planned, "revise"))
    assert before == after


def test_a_plan_at_the_ceiling_is_still_a_chain() -> None:
    """Verifies truncating at the ceiling never leaves a dangling dependency."""
    task = "\n".join(f"objective {index}" for index in range(MAX_TASKS_PER_PLAN + 3))
    planned = TaskPlanner().plan(task)
    ids = {planned_task.id for planned_task in planned}
    assert all(set(item.depends_on) <= ids for item in planned)


def test_assignees_rotate_when_wording_gives_no_hint() -> None:
    """Verifies neutral objectives are spread across the available roles."""
    planned = TaskPlanner().plan("step one\nstep two\nstep three")
    # The rotation is positional, so assert on the sequence rather than on a
    # set size that would still pass if two roles collapsed into one.
    assert [item.assignee for item in planned] == ["researcher", "executor", "writer"], (
        "the rotation is positional"
    )


def test_every_planned_task_survives_the_wire_shape() -> None:
    """Verifies nothing the planner sets is dropped on the way to the console."""
    for planned_task in TaskPlanner().plan("gather\nwrite"):
        wire = planned_task.to_wire()
        assert wire["id"] == planned_task.id
        assert wire["assignee"] == planned_task.assignee
        assert wire["dependsOn"] == list(planned_task.depends_on)


def test_replanning_nothing_yields_nothing() -> None:
    """Verifies replanning an empty plan is a no-op rather than an error."""
    assert TaskPlanner().replan((), "revise") == ()


def test_fanned_out_objectives_are_all_roots() -> None:
    """Verifies parallel planning leaves every task depending on nothing."""
    planned = TaskPlanner().fan_out(("first", "second", "third"))
    assert all(task.depends_on == () for task in planned)


def test_fanning_out_nothing_plans_nothing() -> None:
    """Verifies an empty objective list fans out to an empty plan."""
    assert TaskPlanner().fan_out(()) == ()


def test_fan_out_respects_the_plan_ceiling() -> None:
    """Verifies fanning out is bounded by the same ceiling as chaining."""
    objectives = tuple(f"objective {index}" for index in range(MAX_TASKS_PER_PLAN + 4))
    assert len(TaskPlanner().fan_out(objectives)) == MAX_TASKS_PER_PLAN, (
        "fan-out shares the chained ceiling"
    )


def test_fanned_out_tasks_still_group_under_themselves() -> None:
    """Verifies each fanned-out task is its own branch for budgeting."""
    planned = TaskPlanner().fan_out(("a", "b"))
    roots = branch_roots(planned)
    assert roots == {task.id: task.id for task in planned}


def test_a_task_records_when_it_ran() -> None:
    """Verifies start and finish stamp the timings the canvas renders."""
    task = PlannedTask(id="task-1", title="a").start(10.0).finish(12.5)
    assert (task.started_at, task.finished_at) == (10.0, 12.5)
    assert task.status == "done"


def test_timings_reach_the_wire_shape() -> None:
    """Verifies the console receives the timings, not just the status."""
    wire = PlannedTask(id="task-1", title="a").start(1.0).to_wire()
    assert wire["startedAt"] == 1.0
    assert wire["finishedAt"] is None


def test_finishing_without_starting_still_stamps_the_end() -> None:
    """Verifies a task that was never marked running can still settle."""
    task = PlannedTask(id="task-1", title="a").finish(4.0)
    assert task.started_at is None, (
        "finishing a task must never invent a start time that nothing actually recorded"
    )
    assert task.finished_at == 4.0


def test_the_wire_shape_is_json_serialisable() -> None:
    """Verifies a planned task survives the trip through a WebSocket frame."""
    import json

    wire = TaskPlanner().plan("gather sources")[0].to_wire()
    assert json.loads(json.dumps(wire))["dependsOn"] == []


def test_task_ids_are_stable_across_identical_plans() -> None:
    """Verifies replanning the same task yields the ids the canvas already has."""
    first = TaskPlanner().plan("one\ntwo")
    second = TaskPlanner().plan("one\ntwo")
    assert [task.id for task in first] == [task.id for task in second]

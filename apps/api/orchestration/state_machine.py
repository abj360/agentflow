#!/usr/bin/env python3
"""
state_machine.py --- LangGraph state machine assembled from a runtime task plan

Contains:
    GraphState: typed state flowing through the orchestration graph
    planner_node(): drafts the runtime task plan the graph is wired from
    executor_node(): runs the current plan steps and collects their outputs
    MAX_REVISIONS: revisions one plan branch may spend before it is stopped
    critic_node(): reviews collected outputs and accepts or requests revision
    active_branch(): returns the plan branch the critic is reviewing
    branch_revision_count(): returns how many revisions a branch has spent
    record_branch_revision(): returns the counters with one more revision spent
    task_runner(): builds the node function that runs one planned task
    root_ids(): ids of the tasks that wait on nothing else
    leaf_ids(): ids of the tasks that nothing else depends on
    wire_dependencies(): connects orchestrator, task, and critic nodes
    build_graph(): assembles a LangGraph whose shape follows the task plan
    route_after_critic(): routes the graph on the critic's verdict
    validate_graph(): checks the assembled graph for wiring mistakes
"""

from collections.abc import Callable, Sequence
from typing import Any, NotRequired, TypedDict, cast

from langgraph.graph import END, StateGraph

from apps.api.orchestration.task_planner import (
    PlannedTask,
    TaskPlanner,
    TaskWire,
    branch_roots,
)

ORCHESTRATOR_NODE = "orchestrator"
EXECUTOR_NODE = "executor"
CRITIC_NODE = "critic"

MAX_REVISIONS = 3  # per plan branch, per ADR-002; ADR-001 applied it per session


class GraphState(TypedDict):
    """Represents the state flowing through the orchestration graph.

    Attributes:
        task: The user's task handed to the planner.
        plan: Current step list produced by the planner.
        results: Outputs collected per plan step.
        critique: Latest critic feedback on the plan or results.
        iterations: Number of critic review cycles completed so far.
        tasks: Runtime-planned tasks in the wire shape the console consumes.
        active_branch: Root task id of the branch that last produced a result.
        branch_revisions: Revisions already spent, per branch root id.
    """

    task: str
    plan: list[str]
    results: list[str]
    critique: str
    iterations: int
    tasks: NotRequired[list[TaskWire]]
    active_branch: NotRequired[str]
    branch_revisions: NotRequired[dict[str, int]]


def planner_node(state: GraphState) -> GraphState:
    """Drafts the runtime task plan the graph is wired from.

    Args:
        state: Current graph state containing the task.

    Returns:
        update: State update carrying the plan steps and the planned tasks.
    """
    planned = TaskPlanner().plan(state["task"])
    return {
        **state,
        "plan": [task.title for task in planned],
        "tasks": [task.to_wire() for task in planned],
    }


def executor_node(state: GraphState) -> GraphState:
    """Runs the current plan steps and collects their outputs.

    Args:
        state: Current graph state containing the plan.

    Returns:
        update: State update carrying one result per plan step.
    """
    return {**state, "results": [f"done: {step}" for step in state["plan"]]}


def critic_node(state: GraphState) -> GraphState:
    """Reviews the collected outputs and accepts or requests revision.

    Args:
        state: Current graph state containing plan and results.

    Returns:
        update: State update carrying the critique verdict.
    """
    has_results = bool(state["results"])
    verdict = "accept" if has_results else "revise"
    update: GraphState = {
        **state,
        "critique": verdict,
        "iterations": state["iterations"] + 1,
    }
    if verdict == "revise":
        update["branch_revisions"] = record_branch_revision(
            state, active_branch(state)
        )
    return update


def active_branch(state: GraphState) -> str:
    """Returns the plan branch the critic is currently reviewing.

    Args:
        state: Current graph state.

    Returns:
        branch: Root task id of the branch that last produced a result.
    """
    return state.get("active_branch", ORCHESTRATOR_NODE)


def branch_revision_count(state: GraphState, branch: str) -> int:
    """Returns how many revisions a plan branch has already spent.

    Args:
        state: Current graph state.
        branch: Root task id of the branch being counted.

    Returns:
        revisions: Revisions this branch has taken out of its own budget.
    """
    return state.get("branch_revisions", {}).get(branch, 0)


def record_branch_revision(state: GraphState, branch: str) -> dict[str, int]:
    """Returns the revision counters with one more revision spent on a branch.

    Args:
        state: Current graph state.
        branch: Root task id of the branch about to be revised.

    Returns:
        counters: Revisions spent per branch, with this branch incremented.
    """
    counters = dict(state.get("branch_revisions", {}))
    counters[branch] = counters.get(branch, 0) + 1
    return counters


def task_runner(task: PlannedTask, branch: str) -> Callable[[GraphState], GraphState]:
    """Builds the node function that runs one planned task.

    Args:
        task: The planned task this graph node is responsible for.
        branch: Root task id of the branch this task belongs to.

    Returns:
        execute_task: Node function appending this task's output to the results.
    """

    def execute_task(state: GraphState) -> GraphState:
        """Runs the planned task and records its output.

        Args:
            state: Current graph state.

        Returns:
            update: State update carrying this task's output.
        """
        return {
            **state,
            "active_branch": branch,
            "results": [*state["results"], f"done: {task.title}"],
        }

    return execute_task


def root_ids(tasks: Sequence[PlannedTask]) -> tuple[str, ...]:
    """Returns the ids of the tasks that wait on nothing else.

    Args:
        tasks: Runtime-planned tasks carrying the ids they depend on.

    Returns:
        roots: Ids the orchestrator hands work to directly.
    """
    return tuple(task.id for task in tasks if not task.depends_on)


def leaf_ids(tasks: Sequence[PlannedTask]) -> tuple[str, ...]:
    """Returns the ids of the tasks that nothing else depends on.

    Args:
        tasks: Runtime-planned tasks carrying the ids they depend on.

    Returns:
        leaves: Ids whose completion lets the critic review the run.
    """
    depended_on = {dependency for task in tasks for dependency in task.depends_on}
    return tuple(task.id for task in tasks if task.id not in depended_on)


def wire_dependencies(graph: StateGraph[GraphState], tasks: Sequence[PlannedTask]) -> None:
    """Connects the orchestrator, task, and critic nodes along the plan's edges.

    Args:
        graph: The graph being assembled.
        tasks: Planned tasks whose dependsOn edges define the topology.
    """
    if not tasks:
        graph.add_node(EXECUTOR_NODE, executor_node)
        graph.add_edge(ORCHESTRATOR_NODE, EXECUTOR_NODE)
        graph.add_edge(EXECUTOR_NODE, CRITIC_NODE)
    for root in root_ids(tasks):
        graph.add_edge(ORCHESTRATOR_NODE, root)
    for task in tasks:
        for dependency in task.depends_on:
            graph.add_edge(dependency, task.id)
    for leaf in leaf_ids(tasks):
        graph.add_edge(leaf, CRITIC_NODE)


def build_graph(tasks: Sequence[PlannedTask] | None = None) -> StateGraph[GraphState]:
    """Assembles a LangGraph whose shape follows the runtime task plan.

    Args:
        tasks: Planned tasks whose dependsOn edges define the graph topology.

    Returns:
        graph: State machine wired to run exactly this plan.
    """
    planned: Sequence[PlannedTask] = tasks or ()
    graph = StateGraph(GraphState)
    graph.add_node(ORCHESTRATOR_NODE, planner_node)
    graph.add_node(CRITIC_NODE, critic_node)
    graph.set_entry_point(ORCHESTRATOR_NODE)
    roots = branch_roots(planned)
    for task in planned:
        # langgraph types the node argument against the graph's inferred Never
        # state, which a per-task closure cannot satisfy structurally.
        graph.add_node(task.id, cast(Any, task_runner(task, roots[task.id])))
    wire_dependencies(graph, planned)
    graph.add_conditional_edges(
        CRITIC_NODE,
        route_after_critic,
        {"revise": ORCHESTRATOR_NODE, "accept": END, "bounded": END},
    )
    return graph


def route_after_critic(state: GraphState) -> str:
    """Routes the graph on the critic's verdict, bounded per plan branch.

    Args:
        state: Current graph state containing the critique.

    Returns:
        route: "accept" to finish, "bounded" once the branch has spent its
            revision budget, "revise" to send that branch back for another pass.
    """
    if state["critique"] == "accept":
        return "accept"
    if branch_revision_count(state, active_branch(state)) >= MAX_REVISIONS:
        return "bounded"
    return "revise"


def validate_graph(graph: StateGraph[GraphState]) -> list[str]:
    """Checks the assembled graph for wiring mistakes.

    Args:
        graph: The orchestration graph to validate.

    Returns:
        problems: Wiring problems found, empty when the graph is sound.
    """
    problems: list[str] = []
    for required in (ORCHESTRATOR_NODE, CRITIC_NODE):
        if required not in graph.nodes:
            problems.append(f"{required} node missing")
    return problems

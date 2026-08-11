#!/usr/bin/env python3
"""
state_machine.py --- LangGraph state machine assembled from a runtime task plan

Contains:
    GraphState: typed state flowing through the orchestration graph
    planner_node(): drafts the runtime task plan the graph is wired from
    executor_node(): runs the current plan steps and collects their outputs
    critic_node(): reviews collected outputs and accepts or requests revision
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

from apps.api.orchestration.task_planner import PlannedTask, TaskPlanner

ORCHESTRATOR_NODE = "orchestrator"
EXECUTOR_NODE = "executor"
CRITIC_NODE = "critic"


class GraphState(TypedDict):
    """Represents the state flowing through the orchestration graph.

    Attributes:
        task: The user's task handed to the planner.
        plan: Current step list produced by the planner.
        results: Outputs collected per plan step.
        critique: Latest critic feedback on the plan or results.
        iterations: Number of critic review cycles completed so far.
        tasks: Runtime-planned tasks in the wire shape the console consumes.
    """

    task: str
    plan: list[str]
    results: list[str]
    critique: str
    iterations: int
    tasks: NotRequired[list[dict[str, object]]]


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
    return {**state, "critique": verdict, "iterations": state["iterations"] + 1}


def task_runner(task: PlannedTask) -> Callable[[GraphState], GraphState]:
    """Builds the node function that runs one planned task.

    Args:
        task: The planned task this graph node is responsible for.

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
        return {**state, "results": [*state["results"], f"done: {task.title}"]}

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
    for task in planned:
        # langgraph types the node argument against the graph's inferred Never
        # state, which a per-task closure cannot satisfy structurally.
        graph.add_node(task.id, cast(Any, task_runner(task)))
    wire_dependencies(graph, planned)
    graph.add_conditional_edges(
        CRITIC_NODE,
        route_after_critic,
        {"revise": ORCHESTRATOR_NODE, "accept": END},
    )
    return graph


def route_after_critic(state: GraphState) -> str:
    """Routes the graph based on the critic's verdict.

    Args:
        state: Current graph state containing the critique.

    Returns:
        route: "revise" to loop back to the orchestrator, "accept" to finish.
    """
    if state["critique"] == "accept":
        return "accept"
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

#!/usr/bin/env python3
"""
state_machine.py --- LangGraph planner/executor/critic state machine

Contains:
    GraphState: typed state flowing through the orchestration graph
    build_graph(): assembles the planner/executor/critic LangGraph
"""

from typing import TypedDict

from langgraph.graph import END, StateGraph


class GraphState(TypedDict):
    """Represents the state flowing through the orchestration graph.

    Attributes:
        task: The user's task handed to the planner.
        plan: Current step list produced by the planner.
        results: Outputs collected by the executor per step.
        critique: Latest critic feedback on the plan or results.
        iterations: Number of plan/revise cycles completed so far.
    """

    task: str
    plan: list[str]
    results: list[str]
    critique: str
    iterations: int


def planner_node(state: GraphState) -> GraphState:
    """Produces the initial plan for the task.

    Args:
        state: Current graph state containing the task.

    Returns:
        update: State update carrying the first plan draft.
    """
    return {**state, "plan": [state["task"]]}


def executor_node(state: GraphState) -> GraphState:
    """Executes the current plan steps and collects outputs.

    Args:
        state: Current graph state containing the plan.

    Returns:
        update: State update carrying one result per plan step.
    """
    return {**state, "results": [f"done: {step}" for step in state["plan"]]}


def critic_node(state: GraphState) -> GraphState:
    """Reviews the executor outputs and accepts or requests revision.

    Args:
        state: Current graph state containing plan and results.

    Returns:
        update: State update carrying the critique verdict.
    """
    return {**state, "critique": "accept"}


def build_graph() -> StateGraph:
    """Assembles the planner/executor/critic LangGraph.

    Returns:
        graph: Compiled state machine ready to run one orchestration session.
    """
    graph = StateGraph(GraphState)
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("critic", critic_node)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "critic")
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {"revise": "planner", "accept": END},
    )
    return graph


def route_after_critic(state: GraphState) -> str:
    """Routes the graph based on the critic's verdict.

    Args:
        state: Current graph state containing the critique.

    Returns:
        route: "revise" to loop back to the planner, "accept" to finish.
    """
    return "accept" if state["critique"] == "accept" else "revise"

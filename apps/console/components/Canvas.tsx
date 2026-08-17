/**
 * Canvas.tsx --- live React Flow rendering layer for one run's task graph
 *
 * Contains:
 *   Canvas: renders a run's planned tasks as a positioned, live-updating graph
 */

"use client";

import ReactFlow, {
  Background,
  type Edge,
  type EdgeTypes,
  type Node,
} from "reactflow";

import type { Approval } from "../lib/api";
import {
  ORCHESTRATOR_ID,
  pairApprovals,
  speciesFor,
  type RunViewerTask,
} from "../lib/graph-model";
import { useRelaxedLayout } from "../hooks/useRelaxedLayout";
import type { PositionedTask } from "../lib/layout";
import { NODE_TYPES } from "./nodes";
import { edgeId } from "../lib/edge-pulse";
import { PulseEdge } from "./PulseEdge";
import type { OrchestratorNodeData } from "./nodes/OrchestratorNode";
import type { TaskNodeData } from "./nodes/TaskNode";

import "reactflow/dist/style.css";

const ORCHESTRATOR_Y = 160;

// React Flow remounts every custom edge when this map is a new object.
const EDGE_TYPES: EdgeTypes = { pulse: PulseEdge };

/**
 * Renders a run's planned tasks as a positioned, live-updating graph.
 *
 * @param props.tasks - Runtime-planned tasks streamed in for this run so far.
 * @param props.approvals - Approval requests currently waiting on a reviewer.
 * @param props.onResolve - Called with the approval a reviewer has decided.
 * @returns The canvas element.
 */
export function Canvas({
  tasks,
  approvals = [],
  onResolve,
}: Readonly<{
  tasks: readonly RunViewerTask[];
  approvals?: readonly Approval[];
  onResolve?: (approvalId: string) => void;
}>) {
  const waiting = pairApprovals(tasks, approvals);
  const placements: readonly PositionedTask[] = useRelaxedLayout(tasks);
  const positions = new Map(
    placements.map((placement) => [placement.id, placement]),
  );

  const nodes: Node<TaskNodeData | OrchestratorNodeData>[] = [
    {
      id: ORCHESTRATOR_ID,
      type: "orchestrator",
      position: { x: 0, y: ORCHESTRATOR_Y },
      draggable: false,
      data: { label: "Orchestrator", taskCount: tasks.length },
    },
    ...tasks.map((task) => ({
      id: task.id,
      type: speciesFor(task),
      position: {
        x: positions.get(task.id)?.x ?? 0,
        y: positions.get(task.id)?.y ?? 0,
      },
      data: {
        title: task.title,
        assignee: task.assignee,
        status: task.status,
        tokens: task.tokens,
        toolCallCount: task.toolCallCount,
        approval: waiting.get(task.id),
        onResolve,
      },
    })),
  ];

  const edges: Edge[] = [
    ...tasks
      .filter((task) => task.dependsOn.length === 0)
      .map((task) => ({
        id: edgeId(ORCHESTRATOR_ID, task.id),
        type: "pulse",
        source: ORCHESTRATOR_ID,
        target: task.id,
        data: { active: false },
      })),
    ...tasks.flatMap((task) =>
      task.dependsOn.map((dependency) => ({
        id: edgeId(dependency, task.id),
        type: "pulse",
        source: dependency,
        target: task.id,
        data: { active: false },
      })),
    ),
  ];

  return (
    <div className="canvas">
      {tasks.length > 0 ? null : (
        <p className="canvas-empty">Waiting for the planner…</p>
      )}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        edgeTypes={EDGE_TYPES}
        fitView
      >
        <Background />
      </ReactFlow>
    </div>
  );
}

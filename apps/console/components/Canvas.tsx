/**
 * Canvas.tsx --- live React Flow rendering layer for one run's task graph
 *
 * Contains:
 *   buildEdges(): turns a plan's dependencies into React Flow edges
 *   Canvas: renders a run's planned tasks as a positioned, live-updating graph
 */

"use client";

import { useMemo } from "react";

import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
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
const NO_ACTIVE_EDGES: ReadonlySet<string> = new Set();

/**
 * Turns a plan's dependencies into the edges React Flow draws.
 *
 * @param tasks - Runtime-planned tasks carrying the ids they depend on.
 * @param lit - Ids of the edges a trace event is currently firing along.
 * @returns edges - One edge per dependency, plus one per root task.
 */
function buildEdges(
  tasks: readonly RunViewerTask[],
  lit: ReadonlySet<string>,
): readonly Edge[] {
  const fromOrchestrator = tasks
    .filter((task) => task.dependsOn.length === 0)
    .map((task) => ({ source: ORCHESTRATOR_ID, target: task.id }));
  const fromDependencies = tasks.flatMap((task) =>
    task.dependsOn.map((dependency) => ({
      source: dependency,
      target: task.id,
    })),
  );
  return [...fromOrchestrator, ...fromDependencies].map(
    ({ source, target }) => ({
      id: edgeId(source, target),
      type: "pulse",
      source,
      target,
      data: { active: lit.has(edgeId(source, target)) },
    }),
  );
}

/**
 * Renders a run's planned tasks as a positioned, live-updating graph.
 *
 * @param props.tasks - Runtime-planned tasks streamed in for this run so far.
 * @param props.approvals - Approval requests currently waiting on a reviewer.
 * @param props.onResolve - Called with the approval a reviewer has decided.
 * @param props.activeEdgeIds - Edges currently lit by a trace event.
 * @returns The canvas element.
 */
export function Canvas({
  tasks,
  approvals = [],
  onResolve,
  activeEdgeIds,
}: Readonly<{
  tasks: readonly RunViewerTask[];
  approvals?: readonly Approval[];
  onResolve?: (approvalId: string) => void;
  activeEdgeIds?: ReadonlySet<string>;
}>) {
  // A stable identity matters: an inline empty Set would rebuild every edge on
  // each render and undo the memo below.
  const lit = activeEdgeIds ?? NO_ACTIVE_EDGES;
  const waiting = pairApprovals(tasks, approvals);
  const placements: readonly PositionedTask[] = useRelaxedLayout(tasks);
  const positions = useMemo(
    () => new Map(placements.map((placement) => [placement.id, placement])),
    [placements],
  );

  const nodes: readonly Node<TaskNodeData | OrchestratorNodeData>[] = [
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

  const edges = useMemo(() => buildEdges(tasks, lit), [tasks, lit]);

  return (
    <div className="canvas">
      {tasks.length > 0 ? null : (
        <p className="canvas-empty">Waiting for the planner…</p>
      )}
      <ReactFlow
        nodes={[...nodes]}
        edges={[...edges]}
        nodeTypes={NODE_TYPES}
        edgeTypes={EDGE_TYPES}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        minZoom={0.2}
      >
        <Background variant={BackgroundVariant.Dots} gap={18} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

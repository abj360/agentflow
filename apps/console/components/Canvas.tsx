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

import { useRelaxedLayout } from "../hooks/useRelaxedLayout";
import type { Approval } from "../lib/api";
import { edgeId } from "../lib/edge-pulse";
import {
  ORCHESTRATOR_ID,
  pairApprovals,
  speciesFor,
  type RunViewerTask,
} from "../lib/graph-model";
import type { PositionedTask } from "../lib/layout";
import { spawnDelayMs } from "../lib/spawn";
import { NODE_TYPES } from "./nodes";
import type { OrchestratorNodeData } from "./nodes/OrchestratorNode";
import type { TaskNodeData } from "./nodes/TaskNode";
import { PulseEdge } from "./PulseEdge";

import "reactflow/dist/style.css";

// The layout centres every column on y=0, so the orchestrator sits there too.
const ORCHESTRATOR_Y = 0;

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
  const started = new Set(
    tasks.filter((task) => task.status !== "pending").map((task) => task.id),
  );
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
      data: {
        active: lit.has(edgeId(source, target)),
        pending: !started.has(target),
      },
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
  const litEdges = activeEdgeIds ?? NO_ACTIVE_EDGES;
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
      data: {
        label: "Orchestrator",
        taskCount: tasks.length,
        doneCount: tasks.filter((task) => task.status === "done").length,
        tokens: tasks.reduce((total, task) => total + task.tokens, 0),
      },
    },
    ...tasks.map((task, index) => ({
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
        retries: task.retries,
        spawnDelay: spawnDelayMs(index),
        toolCallCount: task.toolCallCount,
        approval: waiting.get(task.id),
        onResolve,
      },
    })),
  ];

  const edges = useMemo(() => buildEdges(tasks, litEdges), [tasks, litEdges]);

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
        nodesConnectable={false}
        elementsSelectable
        panOnScroll
      >
        <Background variant={BackgroundVariant.Dots} gap={18} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

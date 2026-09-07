/**
 * Canvas.tsx --- the live task graph one run is drawn as
 *
 * Contains:
 *   NO_ACTIVE_EDGES: the shared empty set a canvas with no live traffic uses
 *   FIT_VIEW_OPTIONS: the framing every fit of the canvas viewport uses
 *   CanvasProps: everything the canvas needs to draw one run
 *   buildEdges(): turns a plan's dependencies into React Flow edges
 *   measuredGraph(): the ids and measured sizes React Flow currently holds
 *   useFitOnMeasuredGraph(): re-frames the viewport once a new node is measured
 *   CanvasSurface: renders the graph inside an established React Flow context
 *   Canvas: renders a run's planned tasks as a positioned, live-updating graph
 */

"use client";

import { useEffect, useMemo } from "react";

import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  ReactFlowProvider,
  useReactFlow,
  useStore,
  type Edge,
  type EdgeTypes,
  type FitViewOptions,
  type Node,
  type ReactFlowState,
} from "reactflow";

import { useRelaxedLayout } from "../hooks/useRelaxedLayout";
import type { Approval } from "../lib/api";
import { edgeId } from "../lib/edge-pulse";
import type { Feedback } from "../hooks/useRunGraph";
import {
  pairApprovals,
  speciesFor,
  type RunViewerTask,
} from "../lib/graph-model";
import type { PositionedTask } from "../lib/layout";
import { spawnDelayMs } from "../lib/spawn";
import { NODE_TYPES } from "./nodes";
import type { TaskNodeData } from "./nodes/TaskNode";
import { PulseEdge } from "./PulseEdge";

import "reactflow/dist/style.css";

// React Flow remounts every custom edge when this map is a new object.
const EDGE_TYPES: EdgeTypes = { pulse: PulseEdge };
const NO_ACTIVE_EDGES: ReadonlySet<string> = new Set<string>();

// maxZoom caps the fit: a run that has only planned its first task would
// otherwise be framed at React Flow's default 2x, and every node that spawned
// after it would land off screen at that magnification. minZoom is the other
// half of that: a seven-node plan fitted into a narrow canvas shrinks until the
// titles cannot be read, and a graph you have to pan is better than one you
// cannot read.
const FIT_VIEW_OPTIONS: FitViewOptions = {
  padding: 0.2,
  maxZoom: 1,
  minZoom: 0.62,
};

export interface CanvasProps {
  tasks: readonly RunViewerTask[];
  feedback?: readonly Feedback[];
  approvals?: readonly Approval[];
  onResolve?: (approvalId: string) => void;
  activeEdgeIds?: ReadonlySet<string>;
  onFocusTask?: (taskId: string | null) => void;
}

/**
 * Turns a plan's dependencies into the edges React Flow draws.
 *
 * An edge whose source has not been revealed yet is left out: React Flow drops
 * an edge with a missing end anyway, and it would flicker in as the node lands.
 *
 * @param tasks - Runtime-planned tasks carrying the ids they depend on.
 * @param lit - Ids of the edges a trace event is currently firing along.
 * @param sentBack - Return paths a critic has sent work along.
 * @returns edges - One edge per dependency between two revealed tasks, plus
 *   one per critic rejection.
 */
function buildEdges(
  tasks: readonly RunViewerTask[],
  lit: ReadonlySet<string>,
  sentBack: readonly Feedback[],
): Edge[] {
  const status = new Map(tasks.map((task) => [task.id, task.status]));
  const returns: Edge[] = sentBack
    .filter((sent) => status.has(sent.from) && status.has(sent.to))
    .map((sent) => ({
      id: `feedback:${edgeId(sent.from, sent.to)}`,
      type: "pulse",
      source: sent.from,
      target: sent.to,
      label: "revise",
      data: { active: false, pending: false, feedback: true, note: sent.note },
    }));
  return returns.concat(
    tasks
      .flatMap((task) =>
        task.dependsOn.map((dependency) => ({
          source: dependency,
          target: task.id,
        })),
      )
      .filter(({ source }) => status.has(source))
      .map(({ source, target }) => {
        const downstream = status.get(target);
        const settled = downstream === "done" || downstream === "failed";
        return {
          id: edgeId(source, target),
          type: "pulse",
          source,
          target,
          data: {
            // An edge fires from the moment it is drawn and stops when the work
            // at its far end settles. Lighting it only from the trace firing left
            // it sweeping forever, because nothing re-renders a quiet canvas.
            active: !settled,
            pending: false,
          },
        };
      }),
  );
}

/**
 * Builds the ids and measured sizes React Flow currently holds for the graph.
 *
 * @param state - React Flow's internal store.
 * @returns signature - One comparable string, empty while nothing is measured.
 */
export function measuredGraph(state: ReactFlowState): string {
  return Array.from(state.nodeInternals.values())
    .map((node) => `${node.id}:${node.width ?? 0}x${node.height ?? 0}`)
    .join("|");
}

/**
 * Re-frames the viewport once a newly spawned node has actually been measured.
 *
 * React Flow's fitView prop only runs on the first render, and the canvas
 * mounts before the planner has emitted anything, so without this a run keeps
 * the framing chosen for an empty graph and every task spawns off screen.
 *
 * This keys on measured sizes rather than on node count because a spawned node
 * reaches the store a render before it is measured, and fitting a node that
 * still reports no dimensions frames the orchestrator on its own.
 */
function useFitOnMeasuredGraph(): void {
  const { fitView } = useReactFlow();
  const measured = useStore(measuredGraph);

  useEffect(() => {
    if (measured.length > 0) {
      fitView(FIT_VIEW_OPTIONS);
    }
  }, [measured, fitView]);
}

/**
 * Renders a run's planned tasks as a positioned, live-updating graph.
 *
 * @param props.tasks - Runtime-planned tasks streamed in for this run so far.
 * @param props.feedback - Return paths a critic has sent work back along.
 * @param props.approvals - Approval requests currently waiting on a reviewer.
 * @param props.onResolve - Called with the approval a reviewer has decided.
 * @param props.activeEdgeIds - Edges currently lit by a trace event.
 * @param props.onFocusTask - Called with the task id a reviewer selects.
 * @returns The canvas element.
 */
function CanvasSurface({
  tasks,
  feedback = [],
  approvals = [],
  onResolve,
  activeEdgeIds,
  onFocusTask,
}: Readonly<CanvasProps>) {
  // A stable identity matters: an inline empty Set would rebuild every edge on
  // each render and undo the memo below.
  const litEdges = activeEdgeIds ?? NO_ACTIVE_EDGES;
  const waiting = useMemo(
    () => pairApprovals(tasks, approvals),
    [tasks, approvals],
  );
  const placements: readonly PositionedTask[] = useRelaxedLayout(tasks);
  const positions = useMemo(
    () => new Map(placements.map((placement) => [placement.id, placement])),
    [placements],
  );

  const nodes: Node<TaskNodeData>[] = useMemo(
    () => [
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
    ],
    [tasks, positions, waiting, onResolve],
  );

  const edges = useMemo(
    () => buildEdges(tasks, litEdges, feedback),
    [tasks, litEdges, feedback],
  );
  useFitOnMeasuredGraph();

  return (
    <div className="canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        edgeTypes={EDGE_TYPES}
        fitView
        fitViewOptions={FIT_VIEW_OPTIONS}
        minZoom={0.2}
        nodesConnectable={false}
        elementsSelectable
        panOnScroll
        proOptions={{ hideAttribution: true }}
        onNodeClick={(unused, node) => onFocusTask?.(node.id)}
        deleteKeyCode={null}
        multiSelectionKeyCode={null}
        onPaneClick={() => onFocusTask?.(null)}
      >
        <Background variant={BackgroundVariant.Dots} gap={18} size={1} />
        <Controls
          showInteractive={false}
          showFitView={false}
          position="bottom-right"
        />
      </ReactFlow>
    </div>
  );
}

/**
 * Renders a run's planned tasks as a positioned, live-updating graph.
 *
 * @param props - Everything the canvas surface renders, passed straight through.
 * @returns The canvas element, inside its own React Flow context.
 */
export function Canvas(props: Readonly<CanvasProps>) {
  return (
    <ReactFlowProvider>
      <CanvasSurface {...props} />
    </ReactFlowProvider>
  );
}

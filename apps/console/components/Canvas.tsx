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
  type Node,
  type NodeTypes,
} from "reactflow";

import { ORCHESTRATOR_ID, type RunViewerTask } from "../lib/graph-model";
import { layoutTasks } from "../lib/layout";
import { OrchestratorNode } from "./nodes/OrchestratorNode";

import "reactflow/dist/style.css";

const ORCHESTRATOR_Y = 160;

// React Flow remounts every custom node when this map is a new object, so it
// has to live outside the component body.
const NODE_TYPES: NodeTypes = { orchestrator: OrchestratorNode };

/**
 * Renders a run's planned tasks as a positioned, live-updating graph.
 *
 * @param props.tasks - Runtime-planned tasks streamed in for this run so far.
 * @returns The canvas element.
 */
export function Canvas({ tasks }: { tasks: readonly RunViewerTask[] }) {
  const placements = layoutTasks(tasks);
  const positions = new Map(
    placements.map((placement) => [placement.id, placement]),
  );

  const nodes: Node[] = [
    {
      id: ORCHESTRATOR_ID,
      type: "orchestrator",
      position: { x: 0, y: ORCHESTRATOR_Y },
      draggable: false,
      data: { label: "Orchestrator", taskCount: tasks.length },
    },
    ...tasks.map((task) => ({
      id: task.id,
      position: {
        x: positions.get(task.id)?.x ?? 0,
        y: positions.get(task.id)?.y ?? 0,
      },
      data: { label: task.title },
    })),
  ];

  const edges: Edge[] = [
    ...tasks
      .filter((task) => task.dependsOn.length === 0)
      .map((task) => ({
        id: `${ORCHESTRATOR_ID}->${task.id}`,
        source: ORCHESTRATOR_ID,
        target: task.id,
      })),
    ...tasks.flatMap((task) =>
      task.dependsOn.map((dependency) => ({
        id: `${dependency}->${task.id}`,
        source: dependency,
        target: task.id,
      })),
    ),
  ];

  return (
    <div className="canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        fitView
      >
        <Background />
      </ReactFlow>
    </div>
  );
}

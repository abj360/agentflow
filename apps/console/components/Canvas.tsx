/**
 * Canvas.tsx --- live React Flow rendering layer for one run's task graph
 *
 * Contains:
 *   Canvas: renders a run's planned tasks as a positioned, live-updating graph
 */

"use client";

import ReactFlow, { Background, type Edge, type Node } from "reactflow";

import type { RunViewerTask } from "../lib/graph-model";
import { layoutTasks } from "../lib/layout";

import "reactflow/dist/style.css";

/**
 * Renders a run's planned tasks as a positioned, live-updating graph.
 *
 * @param props.tasks - Runtime-planned tasks streamed in for this run so far.
 * @returns The canvas element.
 */
export function Canvas({ tasks }: { tasks: readonly RunViewerTask[] }) {
  const placements = layoutTasks(tasks);
  const positions = new Map(placements.map((placement) => [placement.id, placement]));

  const nodes: Node[] = tasks.map((task) => ({ id: task.id, position: { x: positions.get(task.id)?.x ?? 0, y: positions.get(task.id)?.y ?? 0 }, data: { label: task.title } }));

  const edges: Edge[] = tasks.flatMap((task) => task.dependsOn.map((dependency) => ({ id: `${dependency}->${task.id}`, source: dependency, target: task.id })));

  return (
    <div className="canvas">
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
      </ReactFlow>
    </div>
  );
}

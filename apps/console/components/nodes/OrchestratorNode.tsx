/**
 * OrchestratorNode.tsx --- the fixed central node every task node hangs off
 *
 * Contains:
 *   OrchestratorNode: renders the run's orchestrator as the canvas centre
 */

"use client";

import { Handle, Position, type NodeProps } from "reactflow";

/**
 * Renders the run's orchestrator as the fixed, larger node at the canvas centre.
 *
 * @param props.data - Label and spawned-task count supplied by the canvas.
 * @returns The orchestrator node element.
 */
export function OrchestratorNode({ data }: NodeProps) {
  return (
    <div className="canvas-node canvas-node--orchestrator">
      <strong>{data.label}</strong>
      <span className="canvas-node__meta">{data.taskCount} tasks</span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

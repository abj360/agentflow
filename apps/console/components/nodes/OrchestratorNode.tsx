/**
 * OrchestratorNode.tsx --- the fixed central node every task node hangs off
 *
 * Contains:
 *   OrchestratorNodeData: what the canvas hands the orchestrator node
 *   OrchestratorNode: renders the run's orchestrator as the canvas centre
 */

"use client";

import { Handle, Position, type NodeProps } from "reactflow";

export interface OrchestratorNodeData {
  label: string;
  taskCount: number;
  doneCount: number;
  tokens: number;
}

/**
 * Renders the run's orchestrator as the fixed, larger node at the canvas centre.
 *
 * @param props.data - Label and spawned-task count supplied by the canvas.
 * @returns The orchestrator node element.
 */
export function OrchestratorNode({ data }: NodeProps<OrchestratorNodeData>) {
  return (
    <div className="canvas-node canvas-node--orchestrator">
      <strong>{data.label}</strong>
      <span className="canvas-node__meta">
        {data.taskCount === 0
          ? "planning"
          : data.taskCount === 1
            ? "1 task"
            : `${data.taskCount} tasks`}
      </span>
      {data.taskCount === 0 ? null : (
        <span className="canvas-node__meta">
          {data.doneCount}/{data.taskCount} done
          {data.tokens === 0 ? null : ` · ${data.tokens} tok`}
        </span>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

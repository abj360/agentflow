/**
 * TaskNode.tsx --- the shared shell every task node species renders inside
 *
 * Contains:
 *   TaskNodeData: what the canvas hands one task node
 *   TaskNode: renders one planned task, spawning in when it first mounts
 */

"use client";

import { Handle, Position, type NodeProps } from "reactflow";

import type { TaskStatus } from "../../lib/graph-model";

export interface TaskNodeData {
  title: string;
  assignee: string;
  status: TaskStatus;
  tokens: number;
  toolCallCount: number;
}

/**
 * Renders one planned task, spawning in when the node first mounts.
 *
 * @param props.data - Title, assignee, status, and cost counters for the task.
 * @returns The task node element.
 */
export function TaskNode({ data }: NodeProps<TaskNodeData>) {
  return (
    <div
      className={`canvas-node canvas-node--spawning canvas-node--${data.status}`}
    >
      <Handle type="target" position={Position.Left} />
      <strong>{data.title}</strong>
      <span className="canvas-node__meta">{data.assignee}</span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

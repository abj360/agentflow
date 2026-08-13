/**
 * ToolCallNode.tsx --- task node species for governed MCP tool calls
 *
 * Contains:
 *   ToolCallNode: renders a tool-call task with its running call count
 */

"use client";

import type { NodeProps } from "reactflow";

import { TaskNode, type TaskNodeData } from "./TaskNode";

/**
 * Renders a tool-call task with its running call count.
 *
 * @param props - Node props React Flow passes straight through to the shell.
 * @returns The tool-call node element.
 */
export function ToolCallNode(props: NodeProps<TaskNodeData>) {
  return (
    <TaskNode
      {...props}
      species="tool-call"
      detail={`${props.data.toolCallCount} calls`}
    />
  );
}

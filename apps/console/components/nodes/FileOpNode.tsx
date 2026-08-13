/**
 * FileOpNode.tsx --- task node species for filesystem writes
 *
 * Contains:
 *   FileOpNode: renders a file-operation task inside the shared shell
 */

"use client";

import type { NodeProps } from "reactflow";

import { TaskNode, type TaskNodeData } from "./TaskNode";

/**
 * Renders a file-operation task inside the shared task node shell.
 *
 * @param props - Node props React Flow passes straight through to the shell.
 * @returns The file-operation node element.
 */
export function FileOpNode(props: NodeProps<TaskNodeData>) {
  return <TaskNode {...props} species="file-op" />;
}

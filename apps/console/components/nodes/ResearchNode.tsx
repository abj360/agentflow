/**
 * ResearchNode.tsx --- the node species retrieval work is drawn as
 *
 * Contains:
 *   ResearchNode: renders a research task inside the shared task node shell
 */

"use client";

import type { NodeProps } from "reactflow";

import { TaskNode, type TaskNodeData } from "./TaskNode";

/**
 * Renders a research task inside the shared task node shell.
 *
 * @param props - Node props React Flow passes straight through to the shell.
 * @returns The research node element.
 */
export function ResearchNode(props: NodeProps<TaskNodeData>) {
  return <TaskNode {...props} species="research" />;
}

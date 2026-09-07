/**
 * index.ts --- the node species React Flow renders each planned task as
 *
 * Contains:
 *   NODE_TYPES: species name to component map handed to React Flow, kept at
 *     module scope so React Flow does not remount every node on each render
 */

import type { NodeTypes } from "reactflow";

import { ApprovalNode } from "./ApprovalNode";
import { FileOpNode } from "./FileOpNode";
import { ResearchNode } from "./ResearchNode";
import { ToolCallNode } from "./ToolCallNode";

export const NODE_TYPES: NodeTypes = {
  research: ResearchNode,
  "tool-call": ToolCallNode,
  "file-op": FileOpNode,
  approval: ApprovalNode,
};

/**
 * index.ts --- the node species React Flow renders each planned task as
 *
 * Contains:
 *   NODE_TYPES: species name to component map handed to React Flow
 */

import type { NodeTypes } from "reactflow";

import { ApprovalNode } from "./ApprovalNode";
import { FileOpNode } from "./FileOpNode";
import { OrchestratorNode } from "./OrchestratorNode";
import { ResearchNode } from "./ResearchNode";
import { ToolCallNode } from "./ToolCallNode";

export const NODE_TYPES: NodeTypes = {
  orchestrator: OrchestratorNode,
  research: ResearchNode,
  "tool-call": ToolCallNode,
  "file-op": FileOpNode,
  approval: ApprovalNode,
};

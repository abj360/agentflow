/**
 * PulseEdge.tsx --- dependency edge that sweeps its dash offset while it fires
 *
 * Contains:
 *   PulseEdgeData: what the canvas tells an edge about its last firing
 *   PulseEdge: renders one dependency edge, sweeping while the edge is active
 */

"use client";

import { getBezierPath, type EdgeProps } from "reactflow";

export interface PulseEdgeData {
  active: boolean;
  pending: boolean;
}

/**
 * Renders one dependency edge, sweeping its stroke while the edge is active.
 *
 * @param props - Edge geometry and firing state React Flow hands the edge.
 * @returns The dependency edge element.
 */
export function PulseEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: EdgeProps<PulseEdgeData>) {
  const [path] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });
  const active = data?.active ?? false;
  const pending = data?.pending ?? false;
  const state = active
    ? " canvas-edge--active"
    : pending
      ? " canvas-edge--pending"
      : "";
  return (
    <path id={id} d={path} fill="none" className={`canvas-edge${state}`} />
  );
}

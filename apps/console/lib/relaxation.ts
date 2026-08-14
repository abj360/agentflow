/**
 * relaxation.ts --- light force relaxation layered on the topological skeleton
 *
 * Contains:
 *   RELAXATION_TICKS: simulation ticks one relaxation pass runs
 *   COLLIDE_RADIUS: minimum gap the simulation keeps between two node centres
 *   RelaxationNode: one placed task while the simulation is running
 *   relaxPositions(): nudges nodes apart without leaving their topological column
 */

import {
  forceCollide,
  forceSimulation,
  forceX,
  forceY,
  type SimulationNodeDatum,
} from "d3-force";

import type { PositionedTask } from "./layout";

export const RELAXATION_TICKS = 60;
export const COLLIDE_RADIUS = 64;

export interface RelaxationNode extends SimulationNodeDatum {
  id: string;
  anchorX: number;
  anchorY: number;
}

/**
 * Nudges nodes apart without letting them drift out of their topological column.
 *
 * The column force stays deliberately stronger than the row force: the layout's
 * readability comes from the topological skeleton, and the simulation is only
 * here to stop nodes in the same column from sitting on top of each other.
 *
 * @param placements - Deterministic positions the topological layout produced.
 * @returns relaxed - The same tasks, nudged apart within their columns.
 */
export function relaxPositions(
  placements: readonly PositionedTask[],
): PositionedTask[] {
  const nodes: RelaxationNode[] = placements.map((placement) => ({
    id: placement.id,
    x: placement.x,
    y: placement.y,
    anchorX: placement.x,
    anchorY: placement.y,
  }));

  forceSimulation(nodes)
    .force(
      "column",
      forceX<RelaxationNode>((node) => node.anchorX).strength(0.9),
    )
    .force("row", forceY<RelaxationNode>((node) => node.anchorY).strength(0.08))
    .force("collide", forceCollide<RelaxationNode>(COLLIDE_RADIUS))
    .stop()
    .tick(RELAXATION_TICKS);

  return nodes.map((node) => ({
    id: node.id,
    x: node.x ?? node.anchorX,
    y: node.y ?? node.anchorY,
  }));
}

/**
 * relaxation.ts --- light force relaxation layered on the topological skeleton
 *
 * Contains:
 *   RELAXATION_TICKS: simulation ticks one relaxation pass runs
 *   NODE_HEIGHT: rendered height a task node occupies on the canvas
 *   COLLIDE_RADIUS: minimum gap the simulation keeps between two node centres
 *   toSimulationNodes(): turns deterministic placements into simulation nodes
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
export const NODE_HEIGHT = 84;

// Half the node height plus breathing room, so two nodes in one column never
// visually touch even at the simulation's closest approach.
export const COLLIDE_RADIUS = NODE_HEIGHT / 2 + 30;

interface RelaxationNode extends SimulationNodeDatum {
  id: string;
  anchorX: number;
  anchorY: number;
}

/**
 * Turns deterministic placements into simulation nodes anchored to them.
 *
 * @param placements - Deterministic positions the topological layout produced.
 * @returns nodes - Simulation nodes carrying their anchor as a restoring force.
 */
function toSimulationNodes(
  placements: readonly PositionedTask[],
): RelaxationNode[] {
  return placements.map((placement) => ({
    id: placement.id,
    x: placement.x,
    y: placement.y,
    anchorX: placement.x,
    anchorY: placement.y,
  }));
}

/**
 * Nudges nodes apart without letting them drift out of their topological column.
 *
 * The column force stays deliberately stronger than the row force: the layout's
 * readability comes from the topological skeleton, and the simulation is only
 * here to stop nodes in the same column from sitting on top of each other.
 *
 * Alpha decay is switched off and the tick count fixed, so the same plan always
 * relaxes to the same positions rather than drifting between renders.
 *
 * @param placements - Deterministic positions the topological layout produced.
 * @returns relaxed - The same tasks, nudged apart within their columns.
 */
export function relaxPositions(
  placements: readonly PositionedTask[],
): readonly PositionedTask[] {
  if (placements.length < 2) {
    return [...placements];
  }
  const nodes = toSimulationNodes(placements);

  forceSimulation(nodes)
    .force(
      "column",
      forceX<RelaxationNode>((node) => node.anchorX).strength(0.9),
    )
    .force("row", forceY<RelaxationNode>((node) => node.anchorY).strength(0.12))
    .force("collide", forceCollide<RelaxationNode>(COLLIDE_RADIUS))
    .alphaDecay(0)
    .stop()
    .tick(RELAXATION_TICKS);

  return nodes.map((node) => ({
    id: node.id,
    x: node.x ?? node.anchorX,
    y: node.y ?? node.anchorY,
  }));
}

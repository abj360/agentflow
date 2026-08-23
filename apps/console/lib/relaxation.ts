/**
 * relaxation.ts --- light force relaxation layered on the topological skeleton
 *
 * Contains:
 *   RELAXATION_TICKS: simulation ticks a small plan's relaxation pass runs
 *   MIN_RELAXATION_TICKS: floor a large plan's relaxation pass settles for
 *   MAX_SIMULATION_NODES: plan size past which the skeleton is used untouched
 *   ticksFor(): the tick budget a plan of a given size is worth spending
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
export const MIN_RELAXATION_TICKS = 18;
export const MAX_SIMULATION_NODES = 120;
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
 * Returns the tick budget a plan of a given size is worth spending.
 *
 * Ticks are quadratic in node count once the collision force dominates, so a
 * long run has to buy fewer of them or the canvas stalls every time it replans.
 *
 * @param count - How many nodes the relaxation pass has to settle.
 * @returns ticks - Ticks to run, never below the floor that keeps nodes apart.
 */
export function ticksFor(count: number): number {
  return Math.max(
    MIN_RELAXATION_TICKS,
    Math.round(RELAXATION_TICKS / Math.max(count / 8, 1)),
  );
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
  if (
    placements.length < 2 ||
    placements.length > MAX_SIMULATION_NODES
  ) {
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
    .tick(ticksFor(nodes.length));

  return nodes.map((node) => ({
    id: node.id,
    x: node.x ?? node.anchorX,
    y: node.y ?? node.anchorY,
  }));
}

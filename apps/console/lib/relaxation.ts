/**
 * relaxation.ts --- the light force pass layered on the topological skeleton
 *
 * Contains:
 *   RELAXATION_TICKS: simulation ticks a small plan's relaxation pass runs
 *   MIN_RELAXATION_TICKS: floor a large plan's relaxation pass settles for
 *   MAX_SIMULATION_NODES: plan size past which the skeleton is used untouched
 *   isWorthSimulating(): whether a plan of a given size earns a simulation pass
 *   ticksFor(): the tick budget a plan of a given size is worth spending
 *   NODE_HEIGHT: the height a task node occupies once it has rendered
 *   COLLIDE_RADIUS: minimum gap the simulation keeps between two node centres
 *   COLUMN_STRENGTH: how hard a node is pulled back to its topological column
 *   ROW_STRENGTH: how hard a node is pulled back to its starting row
 *   toSimulationNodes(): turns deterministic placements into simulation nodes
 *   NOTHING_PINNED: the empty pin set a first relaxation pass starts from
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

// The column force has to dominate: the topological skeleton is what makes the
// graph readable, and the simulation only breaks ties inside a column.
export const COLUMN_STRENGTH = 0.9;
export const ROW_STRENGTH = 0.12;

const NOTHING_PINNED: ReadonlyMap<string, PositionedTask> = new Map();
export const NODE_HEIGHT = 78;

// Half the node height plus breathing room, so two nodes in one column never
// visually touch even at the simulation's closest approach.
export const COLLIDE_RADIUS = NODE_HEIGHT / 2 + 26;

interface RelaxationNode extends SimulationNodeDatum {
  readonly id: string;
  readonly anchorX: number;
  readonly anchorY: number;
}

/**
 * Reports whether a plan of a given size is worth running the simulation on.
 *
 * @param count - How many nodes the relaxation pass would have to settle.
 * @returns worthwhile - False for a trivial plan and for one past the ceiling.
 */
function isWorthSimulating(count: number): boolean {
  return count >= 2 && count < MAX_SIMULATION_NODES;
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
  pinned: ReadonlyMap<string, PositionedTask>,
): RelaxationNode[] {
  return placements.map((placement) => {
    const settled = pinned.get(placement.id);
    if (settled === undefined) {
      return {
        id: placement.id,
        x: placement.x,
        y: placement.y,
        anchorX: placement.x,
        anchorY: placement.y,
      };
    }
    return {
      id: placement.id,
      x: settled.x,
      y: settled.y,
      fx: settled.x,
      fy: settled.y,
      anchorX: settled.x,
      anchorY: settled.y,
    };
  });
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
 * Nodes the caller has already settled are pinned rather than re-simulated. A
 * run that spawns a task every few seconds would otherwise re-solve the whole
 * graph on each spawn, and every historical node would visibly jump.
 *
 * @param placements - Deterministic positions the topological layout produced.
 * @param pinned - Positions already settled on screen, which must not move.
 * @returns relaxed - The same tasks, nudged apart within their columns.
 */
export function relaxPositions(
  placements: readonly PositionedTask[],
  pinned: ReadonlyMap<string, PositionedTask> = NOTHING_PINNED,
): readonly PositionedTask[] {
  if (!isWorthSimulating(placements.length)) {
    return [...placements];
  }
  const nodes = toSimulationNodes(placements, pinned);

  forceSimulation(nodes)
    .force(
      "column",
      forceX<RelaxationNode>((node) => node.anchorX).strength(COLUMN_STRENGTH),
    )
    .force(
      "row",
      forceY<RelaxationNode>((node) => node.anchorY).strength(ROW_STRENGTH),
    )
    .force("collide", forceCollide<RelaxationNode>(COLLIDE_RADIUS))
    .alpha(1)
    .alphaDecay(0)
    .stop()
    .tick(ticksFor(nodes.length));

  return nodes.map((node) => ({
    id: node.id,
    x: node.x ?? node.anchorX,
    y: node.y ?? node.anchorY,
  }));
}

/**
 * edge-pulse.ts --- how long a dependency edge stays lit after a trace event fires
 *
 * Contains:
 *   PULSE_DURATION_MS: how long an edge stays active after it fires
 *   EdgePulse: one edge firing, with the moment it started
 *   edgeId(): builds the canvas id for the edge between two task nodes
 *   recordPulse(): folds one firing into the pulse list, dropping expired ones
 *   activeEdges(): the edge ids still lit at a given moment
 */

export const PULSE_DURATION_MS = 900;

export interface EdgePulse {
  id: string;
  firedAt: number;
}

/**
 * Builds the canvas id for the edge between two task nodes.
 *
 * @param source - Id of the task the edge leaves.
 * @param target - Id of the task the edge enters.
 * @returns id - Stable edge id shared by the canvas and the pulse list.
 */
export function edgeId(source: string, target: string): string {
  return `${source}->${target}`;
}

/**
 * Folds one edge firing into the pulse list, dropping the ones that have expired.
 *
 * @param pulses - Firings recorded so far.
 * @param id - Id of the edge that just fired.
 * @param now - Milliseconds since the epoch at the moment of the firing.
 * @returns pulses - Live firings, with this edge's firing restarted.
 */
export function recordPulse(
  pulses: readonly EdgePulse[],
  id: string,
  now: number,
): EdgePulse[] {
  const live = pulses.filter(
    (pulse) => pulse.id !== id && now - pulse.firedAt < PULSE_DURATION_MS,
  );
  return [...live, { id, firedAt: now }];
}

/**
 * Returns the edge ids that are still lit at a given moment.
 *
 * @param pulses - Firings recorded so far.
 * @param now - Milliseconds since the epoch to evaluate the pulses at.
 * @returns active - Ids of the edges still inside their pulse window.
 */
export function activeEdges(
  pulses: readonly EdgePulse[],
  now: number,
): Set<string> {
  return new Set(
    pulses
      .filter((pulse) => now - pulse.firedAt < PULSE_DURATION_MS)
      .map((pulse) => pulse.id),
  );
}

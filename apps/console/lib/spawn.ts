/**
 * spawn.ts --- the timing a newly planned task node mounts with
 *
 * Contains:
 *   SPAWN_STAGGER_MS: gap between two nodes spawning out of the same batch
 *   MAX_SPAWN_DELAY_MS: ceiling so a large plan does not crawl onto the canvas
 *   spawnDelayMs(): the delay a node at a given position waits before spawning
 */

export const SPAWN_STAGGER_MS = 40;
export const MAX_SPAWN_DELAY_MS = 360;

/**
 * Returns how long a node waits before its spawn animation starts.
 *
 * A whole plan arrives in one frame, so without a stagger every node would
 * appear at the same instant and the graph would read as a jump cut.
 *
 * @param index - Zero-based position of the node in the spawning batch.
 * @returns delay - Milliseconds to wait, capped so long plans still land quickly.
 */
export function spawnDelayMs(index: number): number {
  return Math.min(Math.max(index, 0) * SPAWN_STAGGER_MS, MAX_SPAWN_DELAY_MS);
}

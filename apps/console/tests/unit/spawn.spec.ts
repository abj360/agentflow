/**
 * spawn.spec.ts --- tests for the staggered node spawn timing
 *
 * Contains:
 *   spawn specs: the stagger between nodes and the ceiling that bounds it
 */

import { expect, test } from "@playwright/test";

import {
  MAX_SPAWN_DELAY_MS,
  SPAWN_STAGGER_MS,
  spawnDelayMs,
} from "../../lib/spawn";

test("the first node spawns immediately", () => {
  expect(spawnDelayMs(0)).toBe(0);
});

test("each node waits one stagger longer than the one before it", () => {
  expect(spawnDelayMs(2) - spawnDelayMs(1)).toBe(SPAWN_STAGGER_MS);
});

test("a long plan stops staggering at the ceiling", () => {
  expect(spawnDelayMs(500)).toBe(MAX_SPAWN_DELAY_MS);
});

/**
 * playwright.config.ts --- test runner configuration for the console suites
 *
 * Contains:
 *   config: the unit and end-to-end projects, and the dev server e2e drives
 */

import { defineConfig, type PlaywrightTestConfig } from "@playwright/test";

const config: PlaywrightTestConfig = defineConfig({
  // The e2e suite drives a live dev server, so one retry absorbs a slow first
  // compile without hiding a real regression behind an endless retry budget.
  retries: 1,
  expect: { timeout: 5_000 },
  reporter: process.env.CI ? "github" : "list",
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
  },
  projects: [
    { name: "unit", testDir: "tests/unit" },
    { name: "e2e", testDir: "e2e" },
  ],
});

export default config;

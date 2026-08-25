/**
 * playwright.config.ts --- test runner configuration for the console suites
 *
 * Contains:
 *   config: unit and end-to-end projects, and the dev server the e2e suite drives
 */

import { defineConfig, type PlaywrightTestConfig } from "@playwright/test";

const config: PlaywrightTestConfig = defineConfig({
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

/**
 * playwright.config.ts --- test runner configuration for the console suites
 *
 * Contains:
 *   config: unit and end-to-end projects, and the dev server the e2e suite drives
 */

import { defineConfig } from "@playwright/test";

const config = defineConfig({
  projects: [
    { name: "unit", testDir: "tests/unit" },
    { name: "e2e", testDir: "e2e" },
  ],
});

export default config;

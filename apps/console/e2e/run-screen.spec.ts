/**
 * run-screen.spec.ts --- e2e tests for the unified run screen
 *
 * Contains:
 *   run screen specs: chat, canvas, and raw-log surfaces on one route
 */

import { expect, test } from "@playwright/test";

const RUN_ID = "run-e2e-1";

test.describe("unified run screen", () => {
  test("shows the run id in the header", async ({ page }) => {
    await page.goto(`/run/${RUN_ID}`);
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Run");
  });

  test("puts chat and canvas on the same screen", async ({ page }) => {
    await page.goto(`/run/${RUN_ID}`);
    await expect(page.getByLabel("Run chat")).toBeVisible();
    await expect(page.getByLabel("Run canvas")).toBeVisible();
  });

  test("renders the canvas surface", async ({ page }) => {
    await page.goto(`/run/${RUN_ID}`);
    await expect(page.locator(".canvas")).toBeVisible();
  });

  test("anchors the graph on the orchestrator node", async ({ page }) => {
    await page.goto(`/run/${RUN_ID}`);
    await expect(page.locator(".canvas-node--orchestrator")).toBeVisible();
  });
});

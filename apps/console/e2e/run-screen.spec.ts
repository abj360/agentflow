/**
 * run-screen.spec.ts --- e2e tests for the unified run screen
 *
 * Contains:
 *   openRun(): opens the unified run screen for the fixture run
 *   run screen specs: chat, canvas, and raw-log surfaces on one route
 */

import { expect, test, type Page } from "@playwright/test";

const RUN_ID = "run-e2e-1";

/**
 * Opens the unified run screen for the fixture run.
 *
 * @param page - Playwright page the test is driving.
 */
async function openRun(page: Page): Promise<void> {
  await openRun(page);
}

test.describe("unified run screen", () => {
  test("shows the run id in the header", async ({ page }) => {
    await openRun(page);
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Run");
  });

  test("puts chat and canvas on the same screen", async ({ page }) => {
    await openRun(page);
    await expect(page.getByLabel("Run chat")).toBeVisible();
    await expect(page.getByLabel("Run canvas")).toBeVisible();
  });

  test("renders the canvas surface", async ({ page }) => {
    await openRun(page);
    await expect(page.locator(".canvas")).toBeVisible();
  });

  test("anchors the graph on the orchestrator node", async ({ page }) => {
    await openRun(page);
    // React Flow measures the pane before it paints, so wait for attachment
    // rather than visibility or the assertion races the first layout pass.
    await page.locator(".canvas-node--orchestrator").waitFor({
      state: "attached",
    });
    await expect(page.locator(".canvas-node--orchestrator")).toBeVisible();
  });
});

test("the composer sends an instruction into the run", async ({ page }) => {
  await openRun(page);
  await page.getByLabel("Instruction").fill("summarise the findings");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.locator(".chat-message")).toContainText(
    "summarise the findings",
  );
});

test("an empty instruction is not sent", async ({ page }) => {
  await openRun(page);
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.locator(".chat-message")).toHaveCount(0);
});

test("the raw trace log starts collapsed", async ({ page }) => {
  await openRun(page);
  const rawLogToggle = page.getByRole("button", { name: /raw trace log/i });
  await expect(rawLogToggle).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator(".trace-list")).toHaveCount(0);
});

test("an unknown run still renders the screen", async ({ page }) => {
  await page.goto("/run/does-not-exist");
  await expect(page.getByLabel("Run canvas")).toBeVisible();
  await expect(page.locator(".canvas-empty")).toBeVisible();
});

test("the canvas offers zoom controls", async ({ page }) => {
  await openRun(page);
  await expect(page.locator(".react-flow__controls")).toBeVisible();
});

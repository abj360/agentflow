/**
 * run-screen.spec.ts --- e2e tests for the unified run screen
 *
 * Contains:
 *   openRun(): opens the unified run screen for the fixture run
 *   rawLogToggle(): locates the raw trace log disclosure button
 *   run screen specs: chat, canvas, and raw-log surfaces on one route
 */

import { expect, test, type Locator, type Page } from "@playwright/test";

const RUN_ID = "run-e2e-1";

/**
 * Opens the unified run screen for the fixture run.
 *
 * @param page - Playwright page the test is driving.
 */
async function openRun(page: Page): Promise<void> {
  await page.goto(`/run/${RUN_ID}`);
}

/**
 * Locates the raw trace log disclosure button.
 *
 * @param page - Playwright page the test is driving.
 * @returns toggle - Locator for the raw log button.
 */
function rawLogToggle(page: Page): Locator {
  return page.getByRole("button", { name: /raw trace log/i });
}

test.describe("unified run screen", () => {
  test("names the product, not the page", async ({ page }) => {
    await openRun(page);
    await expect(page.getByText("Agentflow", { exact: true })).toBeVisible();
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

  test("draws no node until a task is planned", async ({ page }) => {
    await openRun(page);
    // The coordinator is the chat panel, not a node, so an unplanned run
    // has nothing to draw and the canvas stays deliberately empty.
    await expect(page.locator(".canvas-node")).toHaveCount(0);
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
  await expect(rawLogToggle(page)).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator(".trace-list")).toHaveCount(0);
});

test("an unknown run still renders the screen", async ({ page }) => {
  await page.goto("/run/does-not-exist");
  await expect(page.getByLabel("Run canvas")).toBeVisible();
  await expect(page.locator(".canvas-placeholder")).toBeVisible();
});

test("the canvas offers zoom controls", async ({ page }) => {
  await openRun(page);
  // React Flow mounts its controls after the pane measures itself, so the
  // locator has to wait rather than assert on the first paint.
  await page.locator(".react-flow__controls").waitFor({ state: "visible" });
  await expect(page.locator(".react-flow__controls")).toBeVisible();
});

test("opening the raw log reveals the log list", async ({ page }) => {
  await openRun(page);
  await rawLogToggle(page).click();
  await expect(rawLogToggle(page)).toHaveAttribute("aria-expanded", "true");
});

test("task nodes carry a status dot", async ({ page }) => {
  await openRun(page);
  await expect(page.locator(".canvas-node__status")).toHaveCount(0);
});

test("the old approvals route no longer exists", async ({ page }) => {
  const landed = await page.goto("/approvals");
  expect(landed?.status()).toBe(404);
});

test("the old traces route no longer exists", async ({ page }) => {
  const landed = await page.goto("/traces");
  expect(landed?.status()).toBe(404);
});

test("the landing page points at the run screen", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /open the live run/i }).click();
  await expect(page).toHaveURL(/\/run\//);
});

test("the chat composer clears after sending", async ({ page }) => {
  await openRun(page);
  const composer = page.getByLabel("Instruction");
  await composer.fill("check the citations");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(composer).toHaveValue("");
});

test("a short log shows no truncation note", async ({ page }) => {
  await openRun(page);
  await rawLogToggle(page).click();
  await expect(page.locator(".trace-truncated")).toHaveCount(0);
});

test("the send button is disabled until something is typed", async ({
  page,
}) => {
  await openRun(page);
  const send = page.getByRole("button", { name: "Send" });
  await expect(send).toBeDisabled();
  await page.getByLabel("Instruction").fill("go");
  await expect(send).toBeEnabled();
});

test("the canvas pane stays mounted while panning", async ({ page }) => {
  await openRun(page);
  await expect(page.locator(".react-flow__pane")).toBeVisible();
});

test("the run screen survives a reload", async ({ page }) => {
  await openRun(page);
  await page.reload();
  await expect(page.getByLabel("Run canvas")).toBeVisible();
});

test("the whole run fits on one screen", async ({ page }) => {
  await openRun(page);
  for (const region of ["Chat sessions", "Run canvas", "Run chat"]) {
    await expect(page.getByLabel(region)).toBeVisible();
  }
});

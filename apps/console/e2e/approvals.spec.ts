#!/usr/bin/env ts-node
/**
 * approvals.spec.ts --- e2e tests for the human-in-the-loop approval flow
 *
 * Contains:
 *   approval queue specs: list, approve, reject flows
 */

import { expect, test } from "@playwright/test";

test.describe("approval queue", () => {
  test("lists pending approvals @smoke", async ({ page }) => {
    await page.goto("/approvals");
    await expect(page.getByRole("heading", { name: "Approvals" })).toBeVisible();
  });
});

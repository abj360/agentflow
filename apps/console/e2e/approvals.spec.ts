#!/usr/bin/env ts-node
/**
 * approvals.spec.ts --- e2e tests for the human-in-the-loop approval flow
 *
 * Contains:
 *   approval queue specs: list, approve, reject flows
 */

import { expect, test } from "@playwright/test";

test.describe("approval queue", () => {
  test("lists pending approvals", async ({ page }) => {
    await page.goto("/approvals");
    await expect(page.getByRole("heading", { name: "Approvals" })).toBeVisible();
  });
});


test("approve removes the card from the queue", async ({ page }) => {
  await page.goto("/approvals");
  const card = page.locator(".approval-card").first();
  await card.getByRole("button", { name: /approve/i }).click();
  await expect(card).toHaveCount(0);
});


test("reject removes the card from the queue", async ({ page }) => {
  await page.goto("/approvals");
  const card = page.locator(".approval-card").first();
  await card.getByRole("button", { name: /reject/i }).click();
  await expect(card).toHaveCount(0);
});


test("empty queue shows the empty state", async ({ page }) => {
  await page.goto("/approvals");
  await expect(page.getByText(/no pending approvals/i)).toBeVisible();
});


test("queue list is visible", async ({ page }) => {
  await page.goto("/approvals");
  await expect(page.locator(".approval-queue")).toBeVisible();
});


test("approval card shows the tool name", async ({ page }) => {
  await page.goto("/approvals");
  const card = page.locator(".approval-card").first();
  await expect(card.locator("strong")).toBeVisible();
});

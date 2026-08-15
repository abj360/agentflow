/**
 * approval-shortcuts.spec.ts --- regression tests for the approval keyboard shortcuts
 *
 * Contains:
 *   decisionForKey specs: which key press maps to which reviewer decision
 */

import { expect, test } from "@playwright/test";

import {
  APPROVE_KEY,
  REJECT_KEY,
  decisionForKey,
} from "../../hooks/useApprovalShortcuts";

test("the approve key records an approval", () => {
  expect(decisionForKey(APPROVE_KEY)).toBe("approved");
});

test("the reject key records a rejection", () => {
  expect(decisionForKey(REJECT_KEY)).toBe("rejected");
});

test("an unbound key records nothing", () => {
  expect(decisionForKey("q")).toBeNull();
});

test("the shortcuts do not collide with each other", () => {
  expect(APPROVE_KEY).not.toBe(REJECT_KEY);
});

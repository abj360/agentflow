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
  hasModifier,
  isTypingTarget,
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

test("a press inside a text field is never a decision", () => {
  const field = { tagName: "INPUT" };
  expect(isTypingTarget(field as unknown as EventTarget)).toBe(true);
});

test("a press on the canvas is a decision", () => {
  const node = { tagName: "DIV" };
  expect(isTypingTarget(node as unknown as EventTarget)).toBe(false);
});

test("a press with no target is not treated as typing", () => {
  expect(isTypingTarget(null)).toBe(false);
});

test("a modifier combination is never a decision", () => {
  expect(hasModifier({ metaKey: true, ctrlKey: false, altKey: false })).toBe(
    true,
  );
});

test("a bare key press carries no modifier", () => {
  expect(hasModifier({ metaKey: false, ctrlKey: false, altKey: false })).toBe(
    false,
  );
});

test("an uppercase press is not a shortcut", () => {
  expect(decisionForKey(APPROVE_KEY.toUpperCase())).toBeNull();
});

test("a content-editable surface counts as typing", () => {
  const editor = { tagName: "DIV", isContentEditable: true };
  expect(isTypingTarget(editor as unknown as EventTarget)).toBe(true);
});

test("a textarea counts as typing", () => {
  const field = { tagName: "TEXTAREA" };
  expect(isTypingTarget(field as unknown as EventTarget)).toBe(true);
});

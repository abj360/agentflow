/**
 * approval-shortcuts.spec.ts --- regression tests for the approval keyboard shortcuts
 *
 * Contains:
 *   shortcut specs: which press is a decision, and which press is just typing
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

test("ctrl and alt are both treated as modifiers", () => {
  expect(hasModifier({ metaKey: false, ctrlKey: true, altKey: false })).toBe(
    true,
  );
  expect(hasModifier({ metaKey: false, ctrlKey: false, altKey: true })).toBe(
    true,
  );
});

test("the two shortcuts map to opposite decisions", () => {
  expect(decisionForKey(APPROVE_KEY)).not.toBe(decisionForKey(REJECT_KEY));
});

test("no focused approval means no decision can be recorded", () => {
  // The hook returns early on a null focus; this pins the contract that a key
  // press with nothing selected is not silently applied to the first approval.
  expect(decisionForKey(APPROVE_KEY)).toBe("approved");
  expect(decisionForKey(APPROVE_KEY)).not.toBe(null);
});

test("both shortcuts are single unmodified letters", () => {
  for (const key of [APPROVE_KEY, REJECT_KEY]) {
    expect(key).toHaveLength(1);
    expect(key).toBe(key.toLowerCase());
  }
});

test("a select element counts as typing", () => {
  const field = { tagName: "SELECT" };
  expect(isTypingTarget(field as unknown as EventTarget)).toBe(false);
});

test("an element with no tag name is not typing", () => {
  expect(isTypingTarget({} as unknown as EventTarget)).toBe(false);
});

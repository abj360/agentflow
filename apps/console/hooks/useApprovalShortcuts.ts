/**
 * useApprovalShortcuts.ts --- keyboard shortcuts for approving and rejecting
 *
 * Contains:
 *   APPROVE_KEY: single press that approves the approval a reviewer is looking at
 *   REJECT_KEY: single press that rejects the approval a reviewer is looking at
 *   hasModifier(): whether a key press carried a modifier the shortcuts ignore
 *   isTypingTarget(): whether a key press landed in a field the user is typing in
 *   decisionForKey(): maps one key press to the decision it records, if any
 *   useApprovalShortcuts(): binds the approve and reject shortcuts for the queue
 */

"use client";

import { useEffect } from "react";

import type { Approval, ApprovalDecision } from "../lib/api";

export const APPROVE_KEY = "a";
export const REJECT_KEY = "r";

/**
 * Reports whether a key press carried a modifier, which shortcuts never do.
 *
 * @param event - The key press being considered.
 * @returns hasModifier - True when a modifier was held down.
 */
export function hasModifier(
  event: Pick<KeyboardEvent, "metaKey" | "ctrlKey" | "altKey">,
): boolean {
  return event.metaKey || event.ctrlKey || event.altKey;
}

/**
 * Reports whether a key press landed in a field the user is typing in.
 *
 * The shortcuts are single letters, so without this a reviewer typing an
 * instruction into the chat composer would approve a tool call by accident.
 *
 * @param target - The element the key press was delivered to.
 * @returns isTyping - True when the press belongs to a text field.
 */
export function isTypingTarget(target: EventTarget | null): boolean {
  // Duck typing rather than instanceof HTMLElement: this runs under the unit
  // runner too, where no DOM constructors exist to check against.
  const element = target as {
    tagName?: string;
    isContentEditable?: boolean;
  } | null;
  if (element?.tagName === undefined) {
    return false;
  }
  return (
    ["INPUT", "TEXTAREA"].includes(element.tagName) ||
    element.isContentEditable === true
  );
}

/**
 * Maps one key press to the decision it records, if it is bound to one.
 *
 * @param key - The KeyboardEvent key that was pressed.
 * @returns decision - The decision the key records, or null when unbound.
 */
export function decisionForKey(key: string): ApprovalDecision | null {
  if (key === APPROVE_KEY) {
    return "approved";
  }
  if (key === REJECT_KEY) {
    return "rejected";
  }
  return null;
}

/**
 * Binds the approve and reject shortcuts while approvals are pending.
 *
 * @param approvals - Pending approvals in the order the queue lists them.
 * @param onDecide - Called with the approval id and the decision the key maps to.
 */
export function useApprovalShortcuts(
  approvals: Approval[],
  onDecide: (approvalId: string, status: ApprovalDecision) => void,
): void {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const [first] = approvals;
      if (first === undefined) {
        return;
      }
      if (isTypingTarget(event.target) || hasModifier(event)) {
        return;
      }
      const decision = decisionForKey(event.key);
      if (decision !== null) {
        onDecide(first.approval_id, decision);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [approvals, onDecide]);
}

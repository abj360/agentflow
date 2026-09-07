/**
 * useStickyToggle.ts --- a boolean the browser remembers between visits
 *
 * Contains:
 *   StickyToggle: the current value and the callback that flips it
 *   useStickyToggle(): reads a remembered boolean and writes back every change
 */

"use client";

import { useCallback, useEffect, useState } from "react";

export interface StickyToggle {
  readonly on: boolean;
  readonly toggle: () => void;
}

/**
 * Reads a remembered boolean and writes every change back to this browser.
 *
 * The remembered value is read after mount rather than during the first render,
 * because the server has no localStorage and rendering one thing on the server
 * and another in the browser is a hydration error, not a preference.
 *
 * @param key - Where the value is remembered.
 * @param initial - What it is before this browser has an opinion.
 * @returns toggle - The current value and the callback that flips it.
 */
export function useStickyToggle(key: string, initial: boolean): StickyToggle {
  const [on, setOn] = useState(initial);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(key);
      if (stored !== null) {
        setOn(stored === "true");
      }
    } catch {
      // a browser with storage blocked still gets a working, unremembered toggle
    }
  }, [key]);

  const toggle = useCallback(() => {
    setOn((previous) => {
      const next = !previous;
      try {
        window.localStorage.setItem(key, String(next));
      } catch {
        // failing to remember the choice must not stop the reviewer making it
      }
      return next;
    });
  }, [key]);

  return { on, toggle };
}

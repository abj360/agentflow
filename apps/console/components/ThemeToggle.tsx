#!/usr/bin/env ts-node
/**
 * ThemeToggle.tsx --- manual light/dark theme switcher
 *
 * Contains:
 *   ThemeToggle: toggles the console between light and dark themes
 */

"use client";

import { useState } from "react";

/**
 * Toggles the console between light and dark themes.
 *
 * @returns The theme toggle button element.
 */
export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  return (
    <button
      aria-pressed={dark}
      onClick={() => {
        const next = dark ? "light" : "dark";
        setDark(!dark);
        document.documentElement.dataset.theme = next;
      }}
    >
      {dark ? "☀ Light" : "☾ Dark"} mode
    </button>
  );
}

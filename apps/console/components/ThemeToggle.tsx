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
  const [isDark, setDark] = useState(false);

  return (
    <button
      className="theme-toggle"
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      aria-pressed={isDark}
      title={isDark ? "Light theme" : "Dark theme"}
      onClick={() => {
        const next = !isDark;
        setDark(next);
        document.documentElement.dataset.theme = next ? "dark" : "light";
      }}
    >
      <svg
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        aria-hidden="true"
      >
        {isDark ? (
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
        ) : (
          <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
          </>
        )}
      </svg>
    </button>
  );
}

/**
 * TraceMenu.tsx --- the raw trace log, reached from the toolbar
 *
 * Contains:
 *   TraceMenu: opens the raw log for the run currently on screen
 */

"use client";

import { useRunTrace } from "./RunTrace";
import { TraceViewer } from "./TraceViewer";

/**
 * Opens the raw log for the run currently on screen.
 *
 * @param props.isOpen - Whether this menu is the one currently open.
 * @param props.onToggle - Called when the reviewer opens or closes the menu.
 * @returns The trace control and, while open, its panel.
 */
export function TraceMenu({
  isOpen,
  onToggle,
}: Readonly<{ isOpen: boolean; onToggle: () => void }>) {
  const logs = useRunTrace();

  return (
    <div className="menu">
      <button
        className="menu__open"
        aria-label="Raw trace log"
        title="Raw trace log"
        aria-expanded={isOpen}
        onClick={onToggle}
      >
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M3 12h4l2.5-6 4 12 2.5-6H21" />
        </svg>
      </button>
      {!isOpen ? null : (
        <div className="menu__panel" role="dialog" aria-label="Raw trace log">
          <TraceViewer events={logs} />
        </div>
      )}
    </div>
  );
}

/**
 * PanelDivider.tsx --- the draggable seam between the canvas and a side panel
 *
 * Contains:
 *   NUDGE_STEP: how far one arrow-key press moves the seam
 *   PanelDivider: renders a separator that resizes the panel beside it
 */

"use client";

import type { PointerEvent as ReactPointerEvent } from "react";

const NUDGE_STEP = 16;

/**
 * Renders a separator that resizes the panel beside it.
 *
 * @param props.label - What the separator is called for assistive technology.
 * @param props.width - Current width of the panel this seam controls.
 * @param props.onResizeStart - Begins a pointer drag on this seam.
 * @param props.onNudge - Moves the seam by a step, for keyboard users.
 * @returns The separator element.
 */
export function PanelDivider({
  label,
  width,
  onResizeStart,
  onNudge,
}: Readonly<{
  label: string;
  width: number;
  onResizeStart: (event: ReactPointerEvent<HTMLElement>) => void;
  onNudge: (step: number) => void;
}>) {
  return (
    <div
      className="panel-divider"
      role="separator"
      aria-orientation="vertical"
      aria-label={label}
      aria-valuenow={Math.round(width)}
      tabIndex={0}
      onPointerDown={onResizeStart}
      onKeyDown={(event) => {
        if (event.key === "ArrowLeft") {
          event.preventDefault();
          onNudge(-NUDGE_STEP);
        }
        if (event.key === "ArrowRight") {
          event.preventDefault();
          onNudge(NUDGE_STEP);
        }
      }}
    />
  );
}

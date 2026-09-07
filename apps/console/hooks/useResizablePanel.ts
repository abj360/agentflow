/**
 * useResizablePanel.ts --- drag-to-resize width for one side panel
 *
 * Contains:
 *   MIN_PANEL_WIDTH: narrowest a side panel may be dragged
 *   MAX_PANEL_WIDTH: widest a side panel may be dragged
 *   PanelEdge: which side of the screen the panel is anchored to
 *   ResizablePanel: the width plus the handlers a divider needs
 *   useResizablePanel(): remembers a panel's width across drags and reloads
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";

export const MIN_PANEL_WIDTH = 180;
export const MAX_PANEL_WIDTH = 560;

export type PanelEdge = "left" | "right";

export interface ResizablePanel {
  width: number;
  startResize: (event: ReactPointerEvent<HTMLElement>) => void;
  nudge: (step: number) => void;
}

/**
 * Clamps a dragged width to what the layout can actually give a side panel.
 *
 * @param width - The width a drag or a stored value asked for.
 * @returns clamped - The width the panel will actually take.
 */
function clamp(width: number): number {
  return Math.min(Math.max(width, MIN_PANEL_WIDTH), MAX_PANEL_WIDTH);
}

/**
 * Remembers one side panel's width across drags and across reloads.
 *
 * The stored width is read in an effect rather than during render because the
 * first paint happens on the server, where there is no storage to read from.
 *
 * @param storageKey - Key this panel's width is remembered under.
 * @param initialWidth - Width to use until a stored one is found.
 * @param edge - Side the panel is anchored to, which flips the drag direction.
 * @returns panel - The current width plus the handlers its divider needs.
 */
export function useResizablePanel(
  storageKey: string,
  initialWidth: number,
  edge: PanelEdge,
): ResizablePanel {
  const [width, setWidth] = useState(initialWidth);
  const latest = useRef(initialWidth);
  latest.current = width;

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(storageKey);
      if (stored !== null) {
        setWidth(clamp(Number(stored)));
      }
    } catch {
      // a browser with storage blocked still gets a usable, unremembered panel
    }
  }, [storageKey]);

  const remember = useCallback(
    (next: number) => {
      try {
        window.localStorage.setItem(storageKey, String(next));
      } catch {
        // losing the remembered width is not worth failing a drag over
      }
    },
    [storageKey],
  );

  const startResize = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      event.preventDefault();
      const originX = event.clientX;
      const originWidth = latest.current;
      const direction = edge === "left" ? 1 : -1;

      const onMove = (move: PointerEvent) => {
        setWidth(clamp(originWidth + direction * (move.clientX - originX)));
      };
      const onRelease = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onRelease);
        document.body.classList.remove("is-resizing");
        remember(latest.current);
      };

      document.body.classList.add("is-resizing");
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onRelease);
    },
    [edge, remember],
  );

  const nudge = useCallback(
    (step: number) => {
      const next = clamp(latest.current + (edge === "left" ? step : -step));
      setWidth(next);
      remember(next);
    },
    [edge, remember],
  );

  return { width, startResize, nudge };
}

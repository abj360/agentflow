/**
 * TopbarActions.tsx --- the toolbar in the top right of the console
 *
 * Contains:
 *   TopbarActions: groups the trace, settings, and theme controls
 */

"use client";

import { useState } from "react";

import { SettingsMenu } from "./SettingsMenu";
import { ThemeToggle } from "./ThemeToggle";
import { TraceMenu } from "./TraceMenu";

/**
 * Groups the trace, settings, and theme controls into one toolbar.
 *
 * @returns The toolbar element.
 */
export function TopbarActions() {
  const [open, setOpen] = useState<"trace" | "settings" | null>(null);

  return (
    <div className="toolbar">
      <TraceMenu
        isOpen={open === "trace"}
        onToggle={() => setOpen(open === "trace" ? null : "trace")}
      />
      <SettingsMenu
        isOpen={open === "settings"}
        onToggle={() => setOpen(open === "settings" ? null : "settings")}
      />
      <ThemeToggle />
    </div>
  );
}

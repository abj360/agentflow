/**
 * RunTrace.tsx --- shares one run's raw log with the toolbar above it
 *
 * Contains:
 *   RunTraceProvider: holds the log lines the toolbar's trace panel reads
 *   useRunTrace(): the log lines currently published by the run on screen
 *   usePublishTrace(): publishes the run's log lines to the toolbar
 */

"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { TraceLogEvent } from "../hooks/useTraceSocket";

interface TraceStore {
  logs: readonly TraceLogEvent[];
  publish: (logs: readonly TraceLogEvent[]) => void;
}

const RunTraceContext = createContext<TraceStore>({
  logs: [],
  publish: () => undefined,
});

/**
 * Holds the log lines the toolbar's trace panel reads.
 *
 * The toolbar sits above the routed page, so the run cannot hand its logs down
 * as props; it publishes them here instead and the toolbar reads them back.
 *
 * @param props.children - The console shell this store wraps.
 * @returns The provider element.
 */
export function RunTraceProvider({
  children,
}: Readonly<{ children: ReactNode }>) {
  const [logs, setLogs] = useState<readonly TraceLogEvent[]>([]);
  const store = useMemo<TraceStore>(() => ({ logs, publish: setLogs }), [logs]);
  return (
    <RunTraceContext.Provider value={store}>
      {children}
    </RunTraceContext.Provider>
  );
}

/**
 * Returns the log lines currently published by the run on screen.
 *
 * @returns logs - Raw log lines, empty when no run has published any.
 */
export function useRunTrace(): readonly TraceLogEvent[] {
  return useContext(RunTraceContext).logs;
}

/**
 * Publishes the run's log lines so the toolbar's trace panel can show them.
 *
 * @param logs - Raw log lines received for the run on screen.
 */
export function usePublishTrace(logs: readonly TraceLogEvent[]): void {
  const { publish } = useContext(RunTraceContext);
  useEffect(() => {
    publish(logs);
  }, [logs, publish]);
}

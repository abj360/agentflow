#!/usr/bin/env ts-node
/**
 * useTraceSocket.ts --- opens and maintains the live trace WebSocket
 *
 * Contains:
 *   useTraceSocket: connects to the trace stream and exposes events
 *   TraceEvent: one event received over the trace stream
 */

import { useEffect, useState } from "react";

export interface TraceEvent {
  kind: string;
  role: string;
  payload: Record<string, unknown>;
}

/**
 * Connects to the trace stream and exposes received events.
 *
 * @param runId - Identifier of the run to stream events for.
 * @returns events - Ordered trace events received so far.
 */
export function useTraceSocket(runId: string): TraceEvent[] {
  const [events, setEvents] = useState<TraceEvent[]>([]);

  useEffect(() => {
    let attempts = 0;
    const connect = () => {
      attempts += 1;
      const socket = new WebSocket(
        `${process.env.NEXT_PUBLIC_WS_URL}/ws/traces?run_id=${runId}`
      );
      socket.onmessage = (message) => {
        const event = JSON.parse(message.data);
        setEvents((prev) => [...prev, event]);
      };
      socket.onclose = () => {
        if (attempts < 5) {
          connect();  // immediate retry while the cap holds
        }
      };
    };
    connect();
  }, [runId]);

  return events;
}

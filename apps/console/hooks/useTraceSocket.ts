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
    let stopped = false;  // set on unmount to halt reconnects
    let attempts = 0;
    let current: WebSocket | null = null;

    const connect = () => {
      attempts += 1;
      const socket = new WebSocket(
        `${process.env.NEXT_PUBLIC_WS_URL}/ws/traces?run_id=${runId}`
      );
      current = socket;
      socket.onopen = () => {
        attempts = 0;  // healthy socket resets the backoff
      };
      socket.onmessage = (message) => {
        if (socket !== current) {
          return;
        }
        const event = JSON.parse(message.data);
        setEvents((prev) => [...prev, event]);
      };
      socket.onclose = () => {
        if (!stopped && attempts < 5) {
          setTimeout(connect, 250 * attempts);
        }
      };
    };

    connect();
    return () => {
      stopped = true;
      current?.close();
    };
  }, [runId]);

  return events;
}

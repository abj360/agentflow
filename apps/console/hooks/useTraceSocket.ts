#!/usr/bin/env ts-node
/**
 * useTraceSocket.ts --- opens and maintains the live trace WebSocket
 *
 * Contains:
 *   useTraceSocket: connects to the trace stream and exposes events
 *   MAX_RECONNECT_ATTEMPTS: reconnect budget before giving up
 *   TraceEvent: one event received over the trace stream
 */

import { useEffect, useState } from "react";

const MAX_RECONNECT_ATTEMPTS = 5;  // then give up and stay offline

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
    let stopped = false;
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
        if (!stopped && attempts < MAX_RECONNECT_ATTEMPTS) {
          const delay = Math.min(250 * 2 ** attempts, 5000);
          setTimeout(connect, delay);  // exponential backoff  // linear backoff
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

/**
 * useTraceSocket.ts --- opens and maintains the live trace WebSocket
 *
 * Contains:
 *   MAX_RECONNECT_ATTEMPTS: reconnect budget before the hook stays offline
 *   TraceLogEvent: one free-form log event received over the trace stream
 *   NodeCreatedEvent: announces a task node the planner has just spawned
 *   EdgeCreatedEvent: announces a dependency edge between two task nodes
 *   NodeStatusChangedEvent: announces a task node's status transition
 *   StructuralEvent: the three frames that shape the canvas graph
 *   TraceEvent: every frame shape the trace stream can deliver
 *   isStructuralEvent(): narrows a trace event to the graph-shaping frames
 *   isLogEvent(): narrows a trace event to the free-form log frames
 *   parseFrame(): parses one socket frame, discarding anything unreadable
 *   useTraceSocket(): connects to the trace stream and exposes received events
 */

"use client";

import { useEffect, useState } from "react";

import type { RunViewerTask, TaskStatus } from "../lib/graph-model";

const MAX_RECONNECT_ATTEMPTS = 5; // then give up and stay offline

export interface TraceLogEvent {
  kind: string;
  role: string;
  payload: Record<string, unknown>;
}

export interface NodeCreatedEvent {
  kind: "node_created";
  task: RunViewerTask;
}

export interface EdgeCreatedEvent {
  kind: "edge_created";
  from: string;
  to: string;
}

export interface NodeStatusChangedEvent {
  kind: "node_status_changed";
  id: string;
  status: TaskStatus;
}

export type StructuralEvent =
  | NodeCreatedEvent
  | EdgeCreatedEvent
  | NodeStatusChangedEvent;

export type TraceEvent = TraceLogEvent | StructuralEvent;

const STRUCTURAL_KINDS = new Set<string>([
  "node_created",
  "edge_created",
  "node_status_changed",
]);

/**
 * Narrows a trace event to the frames that shape the canvas graph.
 *
 * @param event - One event received over the trace stream.
 * @returns isStructural - True when the event creates or updates a graph node or edge.
 */
export function isStructuralEvent(event: TraceEvent): event is StructuralEvent {
  return STRUCTURAL_KINDS.has(event.kind);
}

/**
 * Narrows a trace event to the free-form log frames the raw viewer lists.
 *
 * @param event - One event received over the trace stream.
 * @returns isLog - True when the event is a plain role/payload log line.
 */
export function isLogEvent(event: TraceEvent): event is TraceLogEvent {
  return !STRUCTURAL_KINDS.has(event.kind);
}

/**
 * Parses one socket frame, discarding anything that is not a readable event.
 *
 * @param frame - Raw text the socket delivered.
 * @returns event - The parsed event, or null when the frame is unusable.
 */
function parseFrame(frame: string): TraceEvent | null {
  try {
    const parsed: unknown = JSON.parse(frame);
    if (typeof parsed !== "object" || parsed === null) {
      return null;
    }
    return "kind" in parsed ? (parsed as TraceEvent) : null;
  } catch (error) {
    if (error instanceof SyntaxError) {
      return null;
    }
    throw error;
  }
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
    if (runId.length === 0) {
      return;
    }
    let stopped = false;
    let attempts = 0;
    let current: WebSocket | null = null;

    const connect = () => {
      attempts += 1;
      const socket = new WebSocket(
        `${process.env.NEXT_PUBLIC_WS_URL}/ws/traces?run_id=${runId}`,
      );
      current = socket;
      socket.onopen = () => {
        attempts = 0; // healthy socket resets the backoff
      };
      socket.onmessage = (message) => {
        if (socket !== current) {
          return; // drop events from a stale socket
        }
        const event = parseFrame(message.data);
        if (event === null) {
          return; // a truncated frame must not take the stream down
        }
        setEvents((prev) => [...prev, event]);
      };
      socket.onclose = () => {
        if (!stopped && attempts < MAX_RECONNECT_ATTEMPTS) {
          const delay = Math.min(250 * 2 ** attempts, 5000);
          setTimeout(connect, delay); // exponential backoff
        }
      };
    };

    connect();
    return () => {
      stopped = true;
      current?.close(); // no leaked sockets on unmount
    };
  }, [runId]);

  return events;
}

/**
 * useTraceSocket.ts --- opens the live trace WebSocket and unpacks its frames
 *
 * Contains:
 *   MAX_RECONNECT_ATTEMPTS: reconnect budget before the hook stays offline
 *   MAX_RETAINED_EVENTS: how many events a single run keeps in memory
 *   TraceLogEvent: one free-form log event received over the trace stream
 *   NodeCreatedEvent: announces a task node the planner has just spawned
 *   EdgeCreatedEvent: announces a dependency edge between two task nodes
 *   NodeStatusChangedEvent: announces a task node's status transition
 *   StructuralEvent: the three frames that shape the canvas graph
 *   GraphDeltaFrame: a batch of structural events delivered as one frame
 *   TraceEvent: every frame shape the trace stream can deliver
 *   isStructuralEvent(): narrows a trace event to the graph-shaping frames
 *   isLogEvent(): narrows a trace event to the free-form log frames
 *   parseFrame(): parses one socket frame, discarding anything unreadable
 *   isGraphDelta(): narrows a parsed frame to the batched graph delta shape
 *   flattenFrame(): unpacks a batched graph delta into the events it carries
 *   TraceStream: the events received so far plus whether the socket is live
 *   useTraceSocket(): connects to the trace stream and exposes received events
 */

"use client";

import { useEffect, useState } from "react";

import type { RunViewerTask, TaskStatus } from "../lib/graph-model";

const MAX_RECONNECT_ATTEMPTS = 5; // then give up and stay offline
const MAX_RETAINED_EVENTS = 2000; // a long run must not grow the list forever

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

export interface GraphDeltaFrame {
  kind: "graph_delta";
  readonly runId: string;
  events: readonly StructuralEvent[];
}

export type TraceEvent = TraceLogEvent | StructuralEvent;

export interface TraceStream {
  readonly events: TraceEvent[];
  readonly isLive: boolean;
}

const STRUCTURAL_KINDS = new Set<string>([
  "node_created",
  "edge_created",
  "node_status_changed",
]);

const GRAPH_DELTA_KIND = "graph_delta";

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
function parseFrame(frame: string): TraceEvent | GraphDeltaFrame | null {
  try {
    const parsed: unknown = JSON.parse(frame);
    if (typeof parsed !== "object" || parsed === null) {
      return null;
    }
    return "kind" in parsed ? (parsed as TraceEvent | GraphDeltaFrame) : null;
  } catch (error) {
    if (error instanceof SyntaxError) {
      return null;
    }
    throw error;
  }
}

/**
 * Narrows a parsed frame to the batched graph delta shape.
 *
 * @param frame - One parsed frame from the trace stream.
 * @returns isDelta - True when the frame carries a batch of structural events.
 */
function isGraphDelta(
  frame: TraceEvent | GraphDeltaFrame,
): frame is GraphDeltaFrame {
  return frame.kind === GRAPH_DELTA_KIND && "events" in frame;
}

/**
 * Unpacks a batched graph delta into the individual events it carries.
 *
 * The API coalesces a whole plan into one frame so the canvas lays out once
 * rather than once per node, so the hook has to undo that before folding.
 *
 * @param frame - One parsed frame from the trace stream.
 * @returns events - The events the frame delivered, in arrival order.
 */
export function flattenFrame(
  frame: TraceEvent | GraphDeltaFrame,
): TraceEvent[] {
  if (isGraphDelta(frame)) {
    return frame.events.length === 0 ? [] : [...frame.events];
  }
  return [frame];
}

/**
 * Connects to the trace stream and exposes received events.
 *
 * @param runId - Identifier of the run to stream events for.
 * @returns stream - Ordered trace events received so far, and the live flag.
 */
export function useTraceSocket(runId: string): TraceStream {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    if (runId.length === 0) {
      setIsLive(false);
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
        setIsLive(true);
      };
      socket.onmessage = (message) => {
        if (socket !== current) {
          return; // drop events from a stale socket
        }
        const frame = parseFrame(message.data);
        if (frame === null) {
          return; // a truncated frame must not take the stream down
        }
        const unpacked = flattenFrame(frame);
        if (unpacked.length > 0) {
          setEvents((prev) =>
            [...prev, ...unpacked].slice(-MAX_RETAINED_EVENTS),
          );
        }
      };
      socket.onclose = () => {
        setIsLive(false);
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

  return { events, isLive };
}

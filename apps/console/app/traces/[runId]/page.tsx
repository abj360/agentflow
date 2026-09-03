/**
 * page.tsx --- run detail drill-down page
 *
 * Contains:
 *   RunDetailPage: shows one run's events and chain status
 */

"use client";

import { use } from "react";
import { RunDetail } from "../../../components/RunDetail";

export default function RunDetailPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = use(params);
  return <RunDetail runId={runId} />;
}

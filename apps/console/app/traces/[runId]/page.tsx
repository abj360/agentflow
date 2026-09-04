/**
 * page.tsx --- run detail drill-down page
 *
 * Contains:
 *   RunDetailPage: shows one run's events and chain status
 */

"use client";

import { RunDetail } from "../../../components/RunDetail";

/**
 * Shows one run's events and chain status.
 *
 * @param props.params - Route parameters carrying the run identifier.
 * @returns The run detail page element.
 */
export default function RunDetailPage({
  params,
}: {
  params: { runId: string };
}) {
  return <RunDetail runId={params.runId} />;
}

#!/usr/bin/env ts-node
/**
 * page.tsx --- human-in-the-loop approval queue page
 *
 * Contains:
 *   ApprovalsPage: lists pending approval requests with actions
 */

"use client";

import { ApprovalQueue } from "../../components/ApprovalQueue";

export default function ApprovalsPage() {
  return (
    <section>
      <h1>Approvals</h1>
      <p>Policy-gated tool calls waiting for a human decision.</p>
      <ApprovalQueue />
    </section>
  );
}

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
      <h1>Approval queue</h1>
      <ApprovalQueue />
    </section>
  );
}

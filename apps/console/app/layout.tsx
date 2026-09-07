/**
 * layout.tsx --- root layout for the agentflow admin console
 *
 * Contains:
 *   RootLayout: wraps every page with the shared shell
 */

import type { Metadata } from "next";

import { AgentflowMark } from "../components/AgentflowMark";
import { RunTraceProvider } from "../components/RunTrace";
import { TopbarActions } from "../components/TopbarActions";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agentflow",
  description: "Live task graph and approvals for one agentflow run",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <RunTraceProvider>
          <header className="topbar">
            <span className="brand">
              <AgentflowMark />
              <span className="brand__word">Agentflow</span>
            </span>
            <TopbarActions />
          </header>
          <main>{children}</main>
        </RunTraceProvider>
      </body>
    </html>
  );
}

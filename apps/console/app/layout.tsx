/**
 * layout.tsx --- root layout for the agentflow admin console
 *
 * Contains:
 *   RootLayout: wraps every page with the shared shell
 */

import type { Metadata } from "next";
import { ThemeToggle } from "../components/ThemeToggle";
import "./globals.css";

export const metadata: Metadata = {
  title: "agentflow console",
  description: "Live task graph and approvals for one agentflow run",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <span className="logo">agentflow console</span>
          <nav>
            <a href="/run/default">Run</a>
            <ThemeToggle />
          </nav>
        </header>
        <main>{children}</main>
        <footer className="footer">agentflow</footer>
      </body>
    </html>
  );
}

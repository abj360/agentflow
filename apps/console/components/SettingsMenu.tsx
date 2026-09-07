/**
 * SettingsMenu.tsx --- what this console is currently pointed at
 *
 * Contains:
 *   API_BASE: the API origin the console talks to
 *   SettingsMenu: reports the model, the API it calls, and the stream state
 */

"use client";

import { useEffect, useState } from "react";

import { readProvider, type Provider } from "../lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Reports what this console is pointed at: the model, the API, and the stream.
 *
 * @param props.isOpen - Whether this menu is the one currently open.
 * @param props.onToggle - Called when the reviewer opens or closes the menu.
 * @returns The settings control and, while open, its panel.
 */
export function SettingsMenu({
  isOpen,
  onToggle,
}: Readonly<{ isOpen: boolean; onToggle: () => void }>) {
  const [provider, setProvider] = useState<Provider | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    let cancelled = false;
    readProvider()
      .then((loaded) => {
        if (!cancelled) {
          setProvider(loaded);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  return (
    <div className="menu">
      <button
        className="menu__open"
        aria-label="Settings"
        title="Settings"
        aria-expanded={isOpen}
        onClick={onToggle}
      >
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.2a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-2.9-1.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0-1.2-2.9H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.4 7l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 2.9-1.2V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 2.9 1.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.2a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
        </svg>
      </button>
      {!isOpen ? null : (
        <div
          className="menu__panel menu__panel--settings"
          role="dialog"
          aria-label="Settings"
        >
          <dl className="facts">
            <dt>Model</dt>
            <dd>
              {provider?.configured === true
                ? `${provider.provider} · ${provider.model}`
                : "not connected"}
            </dd>
            <dt>API</dt>
            <dd>{API_BASE}</dd>
          </dl>
          <p className="facts__note">
            Connect a provider from the model button in the chat panel.
          </p>
        </div>
      )}
    </div>
  );
}

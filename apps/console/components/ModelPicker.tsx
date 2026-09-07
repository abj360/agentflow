/**
 * ModelPicker.tsx --- choosing the model the team reasons through
 *
 * Contains:
 *   PROVIDER_LABELS: how each provider name is written for a reader
 *   KEY_HINTS: the credential shape each provider issues
 *   Step: which panel of the picker is open
 *   PickerRow: one selectable row in the picker's list
 *   ModelPicker: picks a provider, takes its key, then pins one of its models
 */

"use client";

import { useEffect, useState } from "react";

import {
  readProvider,
  writeModel,
  writeProvider,
  type Provider,
} from "../lib/api";

const PROVIDER_LABELS: Readonly<Record<string, string>> = {
  claude: "Claude",
  openai: "OpenAI",
};

const KEY_HINTS: Readonly<Record<string, string>> = {
  claude: "sk-ant-…",
  openai: "sk-…",
};

type Step = "closed" | "provider" | "key" | "loading" | "model";

/**
 * Renders one selectable row in the picker's list.
 *
 * Rows are flat rather than boxed: a list of eleven bordered rectangles reads
 * as eleven separate controls, when what it is is one choice with eleven
 * answers.
 *
 * @param props.label - What the row offers.
 * @param props.isCurrent - Whether this row is already in use.
 * @param props.onSelect - Called when the reviewer picks this row.
 * @returns The picker row element.
 */
function PickerRow({
  label,
  isCurrent = false,
  onSelect,
}: Readonly<{
  label: string;
  isCurrent?: boolean;
  onSelect: () => void;
}>) {
  return (
    <button
      className="picker__row"
      aria-current={isCurrent}
      onClick={onSelect}
      type="button"
    >
      <span className="picker__row-label">{label}</span>
      <span className="picker__row-mark" aria-hidden="true">
        {isCurrent ? "✓" : ""}
      </span>
    </button>
  );
}

/**
 * Picks the model the team reasons through and takes the credential for it.
 *
 * Provider and model are two separate choices on purpose: an account usually
 * reaches several models, and being handed whichever one the provider defaults
 * to is not the same as choosing. The key goes straight to the API, which
 * verifies it before keeping it, so a mistyped key is refused here rather than
 * at the first goal. Nothing is kept in this browser and nothing is read back.
 *
 * @returns The model picker control and, while open, its panel.
 */
export function ModelPicker() {
  const [step, setStep] = useState<Step>("closed");
  const [provider, setProvider] = useState<Provider | null>(null);
  const [chosen, setChosen] = useState("");
  const [key, setKey] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
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
  }, []);

  const connect = () => {
    setStep("loading");
    setError(null);
    writeProvider(chosen, key.trim())
      .then((loaded) => {
        setProvider(loaded);
        setKey("");
        setStep("model");
      })
      .catch((failure: Error) => {
        setError(failure.message);
        setStep("key");
      });
  };

  const pin = (model: string) => {
    setStep("loading");
    setError(null);
    writeModel(model)
      .then((loaded) => {
        setProvider(loaded);
        setStep("closed");
      })
      .catch((failure: Error) => {
        setError(failure.message);
        setStep("model");
      });
  };

  const ready = provider?.configured === true;
  const label = ready
    ? `${PROVIDER_LABELS[provider.provider] ?? provider.provider} · ${provider.model}`
    : "Choose model provider";
  const providerName = PROVIDER_LABELS[chosen] ?? chosen;
  const title =
    step === "provider"
      ? "Choose a provider"
      : step === "model"
        ? "Choose a model"
        : `Connect ${providerName}`;
  const canGoBack = step !== "provider";

  return (
    <div className="picker">
      <button
        className="picker__open"
        aria-label={label}
        title={label}
        aria-expanded={step !== "closed"}
        data-ready={ready}
        type="button"
        onClick={() => {
          setError(null);
          setStep(step !== "closed" ? "closed" : ready ? "model" : "provider");
        }}
      >
        <svg
          width="13"
          height="13"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.9"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M12 3v3M12 18v3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M3 12h3M18 12h3M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1" />
          <circle cx="12" cy="12" r="3.2" />
        </svg>
        <span className="picker__label">
          {ready ? provider.model : "Model"}
        </span>
      </button>

      {step === "closed" ? null : (
        <div className="picker__panel" role="dialog" aria-label={title}>
          <header className="picker__head">
            {!canGoBack ? null : (
              <button
                className="picker__back"
                aria-label="Back to providers"
                title="Back to providers"
                type="button"
                onClick={() => {
                  setError(null);
                  setStep("provider");
                }}
              >
                &#8249;
              </button>
            )}
            <p className="picker__title">{title}</p>
            <button
              className="picker__close"
              aria-label="Close"
              title="Close"
              type="button"
              onClick={() => setStep("closed")}
            >
              &times;
            </button>
          </header>

          {step === "provider" ? (
            <div className="picker__list">
              {(provider?.providers ?? ["claude", "openai"]).map((name) => (
                <PickerRow
                  key={name}
                  label={PROVIDER_LABELS[name] ?? name}
                  isCurrent={ready && provider.provider === name}
                  onSelect={() => {
                    setChosen(name);
                    setError(null);
                    setStep("key");
                  }}
                />
              ))}
            </div>
          ) : null}

          {step === "key" || step === "loading" ? (
            <div className="picker__form">
              <input
                className="picker__key"
                type="password"
                autoComplete="off"
                autoFocus
                aria-label={`${providerName} API key`}
                placeholder={KEY_HINTS[chosen] ?? "API key"}
                value={key}
                disabled={step === "loading"}
                onChange={(event) => setKey(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && key.trim().length > 0) {
                    connect();
                  }
                }}
              />
              <button
                className="picker__connect"
                disabled={step === "loading" || key.trim().length === 0}
                type="button"
                onClick={connect}
              >
                {step === "loading" ? "Checking…" : "Connect"}
              </button>
              <p className="picker__note">
                Verified now, then held by the API for this process. Never
                stored in this browser.
              </p>
            </div>
          ) : null}

          {step === "model" ? (
            <div className="picker__list picker__list--scroll">
              {(provider?.models ?? []).map((model) => (
                <PickerRow
                  key={model}
                  label={model}
                  isCurrent={model === provider?.model}
                  onSelect={() => pin(model)}
                />
              ))}
            </div>
          ) : null}

          {error === null ? null : (
            <p className="picker__error" role="alert">
              {error}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

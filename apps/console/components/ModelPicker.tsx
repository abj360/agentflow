/**
 * ModelPicker.tsx --- choosing the model the team reasons through
 *
 * Contains:
 *   PROVIDER_LABELS: how each provider name is written for a reader
 *   Step: which panel of the picker is open
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

type Step = "closed" | "provider" | "key" | "loading" | "model";

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
  const pill = ready ? provider.model : "Model";
  const open = () => {
    setError(null);
    setStep(ready ? "model" : "provider");
  };

  return (
    <div className="picker">
      <button
        className="picker__open"
        aria-label={label}
        title={label}
        aria-expanded={step !== "closed"}
        data-ready={ready}
        onClick={() => (step === "closed" ? open() : setStep("closed"))}
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
        <span className="picker__label">{pill}</span>
      </button>

      {step === "closed" ? null : (
        <div className="picker__panel" role="dialog" aria-label={label}>
          {step === "provider" ? (
            <>
              <p className="picker__title">Choose model provider</p>
              {(provider?.providers ?? ["claude", "openai"]).map((name) => (
                <button
                  key={name}
                  className="picker__choice"
                  onClick={() => {
                    setChosen(name);
                    setStep("key");
                  }}
                >
                  {PROVIDER_LABELS[name] ?? name}
                </button>
              ))}
            </>
          ) : null}

          {step === "key" || step === "loading" ? (
            <>
              <p className="picker__title">
                Enter {PROVIDER_LABELS[chosen] ?? chosen} API key
              </p>
              <input
                className="picker__key"
                type="password"
                autoComplete="off"
                autoFocus
                placeholder={chosen === "openai" ? "sk-..." : "sk-ant-..."}
                value={key}
                disabled={step === "loading"}
                onChange={(event) => setKey(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && key.trim().length > 0) {
                    connect();
                  }
                }}
              />
              {error === null ? null : (
                <p className="picker__error" role="alert">
                  {error}
                </p>
              )}
              <button
                className="picker__connect"
                disabled={step === "loading" || key.trim().length === 0}
                onClick={connect}
              >
                {step === "loading" ? "Loading…" : "Connect"}
              </button>
              <p className="picker__note">
                Held by the API for this process. Never stored in this browser.
              </p>
            </>
          ) : null}

          {step === "model" ? (
            <>
              <p className="picker__title">Choose model</p>
              <div className="picker__models">
                {(provider?.models ?? []).map((model) => (
                  <button
                    key={model}
                    className="picker__choice"
                    aria-current={model === provider?.model}
                    onClick={() => pin(model)}
                  >
                    {model}
                  </button>
                ))}
              </div>
              {error === null ? null : (
                <p className="picker__error" role="alert">
                  {error}
                </p>
              )}
              <button
                className="picker__switch"
                onClick={() => {
                  setError(null);
                  setStep("provider");
                }}
              >
                Use a different provider
              </button>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}

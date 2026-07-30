# Contributing to agentflow

Thanks for helping out. This project runs on a fork-and-PR workflow with five core
maintainers; external contributors follow the same path.

## Workflow

1. **Fork** `abj360/agentflow` under your own GitHub account.
2. **Branch** from `main` using `<type>/<short-description>`, e.g.
   `feat/rrf-fusion`, `fix/audit-index`. One logical change per branch.
3. **Commit** small, atomic changes using conventional prefixes: `feat`, `fix`,
   `perf`, `refactor`, `test`, `chore`, `docs`, `ci`, `style`. Each commit should
   revert cleanly on its own. Commit as yourself — your own configured git
   identity, never a tool's default and no generated-with trailers.
4. **Push only your own branches to your own fork** — never to someone else's
   fork or to `origin` directly.
5. **Open a PR** into `abj360/agentflow:main`. Peter (or another maintainer)
   reviews and merges in date order and pushes `main`.

## Local setup

Everything is dockerized:

```bash
cp .env.example .env
scripts/run-local.sh        # == docker compose -f docker/docker-compose.yml up --build
```

For direct Python work: `pip install -e ".[dev]" -e packages/core` (Python 3.12+),
or `pip install -r requirements.txt` for runtime-only dependencies.

## Pre-merge checklist

- [ ] `ruff check . && ruff format --check .` clean
- [ ] `mypy apps packages` clean (strict)
- [ ] `pytest tests/unit tests/integration` green
- [ ] Every new function/class has a verb-first docstring (Args/Returns/Attributes where relevant)
- [ ] No commented-out code; comments only for genuinely non-obvious logic
- [ ] Tests added alongside the change, and they can actually fail
- [ ] Committed as yourself — no tool identity, no AI co-author trailer
- [ ] `docker compose -f docker/docker-compose.yml up --build` still boots cleanly

## Conventions

- **Python:** Ruff for lint and format, `mypy --strict`, 100-char lines, double quotes.
- **TypeScript/React:** ESLint + Prettier, `tsc --strict`, same line length.
- **Tests:** live next to what they test under `tests/` and must assert real
  behavior, not mocks that always succeed.
- **Secrets:** never in code — `.env` only, and `.env` is gitignored.
- **Issues:** open them under your own GitHub identity with a clear repro or a
  concrete proposal; maintainers triage weekly.

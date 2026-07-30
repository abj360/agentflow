# agentflow

A production multi-agent orchestrator: planner/executor/synthesizer/critic roles,
a hash-chained replayable audit log, MCP tool governance, and cost-aware circuit
breakers — with a Next.js console for human-in-the-loop approvals.

## Architecture

```
Console (Next.js) --WebSocket--> API (FastAPI)
                                    |
                          Orchestration loop (LangGraph)
                                    |
                +-------------------+-------------------+
           Audit log (Postgres)  Policy engine (YAML)  MCP servers
```

## Quickstart (one command, fully dockerized)

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
# console on :3000, api on :8000, postgres on :5432, redis on :6379
```

Migrations run automatically on api container startup. No local Python/Node install needed.
Prefer a script? `scripts/run-local.sh` does the same thing.

## Governance

Tool calls are evaluated against `apps/api/policy/schema.yaml` before execution;
high-risk actions route to the approval queue in the console. The schema format is
documented in `docs/policy-schema.md`.

## Load & chaos testing

```bash
locust -f tests/load/locustfile.py
pytest tests/chaos/
```

## Docs

- `docs/adr/ADR-001-orchestration-pattern.md` — the four-role loop and why it is bounded
- `docs/adr/ADR-002-audit-trace-format.md` — the hash-chained audit event format
- `docs/policy-schema.md` — the governance policy schema reference

## License

MIT — see [LICENSE](LICENSE). Contributions welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).

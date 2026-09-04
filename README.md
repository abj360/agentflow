<div align="center">

<img src="docs/media/wordmark.png" alt="agentflow" width="520" />

[![python 3.12+](https://img.shields.io/badge/Python%203.12+-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![fastapi](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](apps/api)
[![langgraph](https://img.shields.io/badge/LangGraph-1C3C3C?logo=langgraph&logoColor=white)](packages/core)
[![mcp](https://img.shields.io/badge/MCP-0d9488)](docs/policy-schema.md)
[![postgresql](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](infra/)
[![redis](https://img.shields.io/badge/Redis-FF4438?logo=redis&logoColor=white)](infra/)
[![next.js](https://img.shields.io/badge/Next.js-000000?logo=nextdotjs&logoColor=white)](apps/console/package.json)
[![docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](docker/)
[![mit](https://img.shields.io/badge/MIT-0d9488?logo=opensourceinitiative&logoColor=white)](LICENSE)

Agentflow is a multi-agent orchestrator that runs a bounded planner, executor,
synthesizer and critic loop over governed MCP tools, routing every high-risk call
to a human approval queue and recording the whole run as a hash-chained audit
trace you can replay.

<img src="docs/media/console.gif" alt="The agentflow console: an orchestration run streaming in, then the approvals it routed to a human" width="940" />

</div>

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
high-risk actions route to the approval queue in the console, where a human
approves or rejects each one before the executor may proceed:

<p align="center">
  <img src="docs/media/approvals.png" alt="The approval queue: policy-gated tool calls awaiting a human decision" width="940" />
</p>

The schema format is documented in `docs/policy-schema.md`.

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

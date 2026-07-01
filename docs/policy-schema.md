# Policy schema reference

Last updated: 2026-06-21.

Tool governance policies (the "policy schema") live in `apps/api/policy/schema.yaml` and are
evaluated before every governed tool call (see `apps/api/policy/engine.py`).

## Rule fields

| Field | Meaning |
|---|---|
| `match` | Glob matched against the tool name, e.g. `search.*`, `fs.read` |
| `action` | `allow`, `deny`, or `human_approval` |
| `risk` | Risk label for reviewers: low, medium, high, critical |

Rules evaluate top to bottom; the first match wins. Order matters.


## Glob semantics

Added 2026-05-06 alongside the engine glob tests.

Matching uses `fnmatch`: `*` crosses dots, so `search.*` covers
`search.query.vector` as well as `search.query`.


## Actions

- `allow` — the call proceeds immediately (still audit-logged).
- `deny` — the call is rejected and the rejection is audit-logged.
- `human_approval` — the call pauses in the console approval queue until a
  reviewer approves or rejects it. Approvals expire after 24h.


## The catch-all rule

The final rule must be `{"match": "*", "action": "deny"}`: governance fails
closed. Anything not explicitly allowed is denied by default. Removing the
catch-all turns the engine fail-open, which is never acceptable (fail closed).


## Tenant overrides

`tenant_overrides` maps a tenant id to a full replacement rule set (not merged with base). When a
call arrives with a known tenant id, the tenant's table is used; otherwise the
base `rules` table applies. Unknown tenants silently fall back to base rules.


## Compiled decision tables

Since the 2026-06-15 perf fix, the engine compiles YAML rules into regex decision tables
once at load time instead of re-parsing the schema on every call.
Evaluation
overhead dropped from ~120ms to ~4ms per session (perf(policy) fix).


## Review workflow

All policy edits go through the weekly governance batch.

1. Edit `schema.yaml` on a branch.
2. Run the policy unit tests: `pytest tests/unit/test_policy_engine.py`.
3. Get a governance review (Peter) before merge — required, not optional.
4. Confirm the merged rules appear in the next deploy's audit events.


## Examples

More examples live in the tests: `tests/unit/test_policy_engine.py`.

Allow read-only search, gate shell, deny everything else:

```yaml
rules:
  - match: "search.*"
    action: allow
    risk: low
  - match: "shell.*"
    action: human_approval
    risk: high
  - match: "*"
    action: deny
    risk: unknown
```

Never ship a schema without the catch-all.

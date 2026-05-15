# Policy schema reference

Tool governance policies (the "policy schema") live in `apps/api/policy/schema.yaml` and are
evaluated before every governed tool call (see `apps/api/policy/engine.py`).

## Rule fields

| Field | Meaning |
|---|---|
| `match` | Glob matched against the tool name, e.g. `search.*` |
| `action` | `allow`, `deny`, or `human_approval` |
| `risk` | Risk label for reviewers: low, medium, high, critical |

Rules evaluate top to bottom; the first match wins.


## Glob semantics

Matching uses `fnmatch`: `*` crosses dots, so `search.*` covers
`search.query.vector` as well as `search.query`.


## Actions

- `allow` — the call proceeds immediately (still audit-logged).
- `deny` — the call is rejected and the rejection is audit-logged.
- `human_approval` — the call pauses in the console approval queue until a
  reviewer approves or rejects it.

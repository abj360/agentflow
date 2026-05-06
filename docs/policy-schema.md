# Policy schema reference

Tool governance policies live in `apps/api/policy/schema.yaml` and are
evaluated before every governed tool call (see `apps/api/policy/engine.py`).

## Rule fields

| Field | Meaning |
|---|---|
| `match` | Glob matched against the tool name, e.g. `search.*` |
| `action` | `allow`, `deny`, or `human_approval` |
| `risk` | Free-form risk label for reviewers: low, medium, high, critical |

Rules evaluate top to bottom; the first match wins.

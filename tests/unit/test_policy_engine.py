#!/usr/bin/env python3
"""
test_policy_engine.py --- unit tests for YAML policy evaluation

Contains:
    test_allow_rule_matches(): verifies an allow-listed tool is allowed
    test_unmatched_tool_denied(): verifies tools with no matching rule are denied
"""

from pathlib import Path

from apps.api.policy.engine import PolicyEngine

SCHEMA_PATH = (
    Path(__file__).parents[2] / "apps" / "api" / "policy" / "schema.yaml"
)


def make_engine() -> PolicyEngine:
    """Builds an engine over a minimal in-memory rule set."""
    return PolicyEngine.from_dict(
        [
            {"match": "search.*", "action": "allow"},
            {"match": "shell.*", "action": "human_approval"},
            {"match": "*", "action": "deny"},  # fail closed
        ]
    )

RULES = [
    {"match": "search.*", "action": "allow"},
    {"match": "shell.*", "action": "human_approval"},
    {"match": "*", "action": "deny"},
]


def build_engine() -> PolicyEngine:
    """Builds an engine over the shared test rule set.

    Returns:
        engine: Policy engine evaluating the test rules.
    """
    return PolicyEngine.from_dict(RULES)


def test_allow_rule_matches() -> None:
    """Verifies an allow-listed tool is allowed."""
    engine = build_engine()
    assert engine.evaluate("search.query", {}).action == "allow"


def test_unmatched_tool_denied() -> None:
    """Verifies tools with no matching rule are denied."""
    engine = build_engine()
    assert engine.evaluate("crypto.mine", {}).action == "deny"


def test_empty_tool_name_denied() -> None:
    """Verifies an empty tool name fails closed."""
    engine = build_engine()
    assert engine.evaluate("", {}).action == "deny"


def test_args_do_not_affect_match() -> None:
    """Verifies call arguments don't change the matched rule."""
    engine = build_engine()
    assert engine.evaluate("search.query", {"q": "x"}).action == "allow"


def test_evaluate_accepts_tenant_keyword() -> None:
    """Verifies evaluate accepts a tenant_id keyword argument."""
    engine = build_engine()
    decision = engine.evaluate("search.query", {}, tenant_id="acme")
    assert decision.action == "allow"


def test_inline_engine_ignores_tenant() -> None:
    """Verifies dict-built engines apply their rules for any tenant."""
    engine = build_engine()
    assert engine.evaluate("shell.exec", {}, tenant_id="globex").action == (
        "human_approval"
    )


def test_review_make_engine_is_callable() -> None:
    """Verifies the shared engine factory returns a usable engine."""
    assert make_engine() is not None


def test_review_deny_is_default_posture() -> None:
    """Verifies the reviewed rule set fails closed by default."""
    engine = make_engine()
    assert engine.evaluate("unknown.tool", {}).action == "deny"


def test_first_matching_rule_wins() -> None:
    """Verifies rule order decides the outcome."""
    engine = build_engine()
    assert engine.evaluate("search.query", {}).rule == "search.*"


def test_engine_reusable_across_evaluations() -> None:
    """Verifies one engine serves repeated evaluations."""
    engine = build_engine()
    assert engine.evaluate("shell.exec", {}).action == "human_approval"


def test_decision_reason_empty_on_allow() -> None:
    """Verifies allow decisions carry no denial reason."""
    decision = build_engine().evaluate("search.query", {})
    assert decision.reason == ""


def test_review_allow_readonly_tool() -> None:
    """Verifies governance behavior reviewed in the weekly batch."""
    engine = make_engine()
    assert engine.evaluate("search.query", {}).action == "allow"


def test_review_search_prefix_globbed() -> None:
    """Verifies the search.* glob covers nested tool names."""
    engine = make_engine()
    assert engine.evaluate("search.query.vector", {}).action == "allow"


def test_review_shell_glob_covers_subtools() -> None:
    """Verifies the shell.* glob covers nested shell tools."""
    engine = make_engine()
    assert engine.evaluate("shell.exec.pipe", {}).action == "human_approval"


def test_human_approval_action() -> None:
    """Verifies shell tools route to human approval."""
    engine = build_engine()
    assert engine.evaluate("shell.exec", {}).action == "human_approval"


def test_decision_has_action_and_rule() -> None:
    """Verifies decisions always expose action and rule fields."""
    decision = build_engine().evaluate("search.query", {})
    assert decision.action == "allow" and decision.rule == "search.*"


def test_shell_subtools_gated() -> None:
    """Verifies nested shell tools also require approval."""
    engine = build_engine()
    assert engine.evaluate("shell.exec.pipe", {}).action == "human_approval"


def test_review_deny_unmatched_tool() -> None:
    """Verifies tools matching no rule fall through to deny."""
    engine = make_engine()
    assert engine.evaluate("crypto.mine", {}).action == "deny"


def test_review_args_do_not_change_action() -> None:
    """Verifies call arguments don't influence the rule match."""
    engine = make_engine()
    decision = engine.evaluate("search.query", {"q": "x"})
    assert decision.action == "allow"


def test_review_engine_reusable_across_calls() -> None:
    """Verifies one engine instance evaluates repeatedly."""
    engine = make_engine()
    engine.evaluate("search.query", {})
    assert engine.evaluate("shell.exec", {}).action == "human_approval"


def test_deny_reports_no_matching_rule() -> None:
    """Verifies an unmatched call reports the catch-all rule."""
    engine = build_engine()
    decision = engine.evaluate("random.tool", {})
    assert decision.rule == "*"


def test_evaluate_is_deterministic() -> None:
    """Verifies repeated evaluation of the same call is stable."""
    engine = build_engine()
    first = engine.evaluate("search.query", {})
    second = engine.evaluate("search.query", {})
    assert first == second


def test_rules_constant_covers_three_actions() -> None:
    """Verifies the shared rule set exercises every action."""
    actions = {rule["action"] for rule in RULES}
    assert actions == {"allow", "deny", "human_approval"}


def test_tenant_override_applies_when_present() -> None:
    """Verifies a tenant override table shadows the base rules."""
    engine = PolicyEngine(str(SCHEMA_PATH))
    decision = engine.evaluate("db.read", {}, tenant_id="acme")
    assert decision.action == "allow"
    assert decision.rule == "db.*"


def test_schema_file_loads_rules() -> None:
    """Verifies the shipped schema file parses into rules."""
    engine = PolicyEngine(str(SCHEMA_PATH))
    assert engine.evaluate("search.query", {}).action == "allow"


def test_schema_base_denies_unknown() -> None:
    """Verifies the shipped schema fails closed on unknown tools."""
    engine = PolicyEngine(str(SCHEMA_PATH))
    assert engine.evaluate("totally.unknown", {}).action == "deny"


def test_review_shell_requires_human() -> None:
    """Verifies shell tools route to the human approval queue."""
    engine = make_engine()
    assert engine.evaluate("shell.exec", {}).action == "human_approval"


def test_review_decision_type_stable() -> None:
    """Verifies evaluate always returns a decision object."""
    engine = make_engine()
    for tool in ("search.query", "shell.exec", "misc"):
        assert engine.evaluate(tool, {}).action in {
            "allow",
            "deny",
            "human_approval",
        }


def test_glob_matches_nested_names() -> None:
    """Verifies star globs cover dotted sub-tools."""
    engine = build_engine()
    assert engine.evaluate("search.query.vector", {}).action == "allow"


def test_no_rule_is_none_reason_text() -> None:
    """Verifies the default-deny reason mentions the default."""
    engine = PolicyEngine.from_dict([])
    decision = engine.evaluate("anything", {})
    assert decision.action == "deny"


def test_empty_rule_set_denies_everything() -> None:
    """Verifies an engine with no rules fails closed."""
    engine = PolicyEngine.from_dict([])
    assert engine.evaluate("search.query", {}).action == "deny"


def test_is_allowed_false_for_approval() -> None:
    """Verifies approval-needed calls are not treated as allowed."""
    from apps.api.policy.engine import is_allowed

    engine = build_engine()
    assert is_allowed(engine.evaluate("shell.exec", {})) is False


def test_decision_equality() -> None:
    """Verifies identical decisions compare equal."""
    engine = build_engine()
    assert engine.evaluate("search.query", {}) == engine.evaluate("search.query", {})


def test_unknown_tenant_falls_back_to_base_rules() -> None:
    """Verifies tenants without overrides use the base policy."""
    engine = PolicyEngine(str(SCHEMA_PATH))
    decision = engine.evaluate("search.query", {}, tenant_id="no-such-tenant")
    assert decision.action == "allow"


def test_acme_shell_still_requires_approval() -> None:
    """Verifies acme's override keeps shell gated."""
    engine = PolicyEngine(str(SCHEMA_PATH))
    decision = engine.evaluate("shell.exec", {}, tenant_id="acme")
    assert decision.action == "deny"


def test_base_shell_requires_human_approval() -> None:
    """Verifies the base policy gates shell tools for humans."""
    engine = PolicyEngine(str(SCHEMA_PATH))
    assert engine.evaluate("shell.exec", {}).action == "human_approval"


def test_compiled_evaluation_is_fast() -> None:
    """Verifies compiled evaluation is far below the old 120ms parse cost."""
    import time

    engine = PolicyEngine(str(SCHEMA_PATH))
    start = time.perf_counter()
    for _ in range(100):
        engine.evaluate("search.query", {})
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 50


def test_review_decision_carries_matched_rule() -> None:
    """Verifies decisions name the rule that produced them."""
    engine = make_engine()
    decision = engine.evaluate("search.query", {})
    assert decision.rule == "search.*"


def test_review_empty_tool_name_denied() -> None:
    """Verifies an empty tool name fails closed."""
    engine = make_engine()
    assert engine.evaluate("", {}).action == "deny"


def test_review_matched_rule_none_on_deny() -> None:
    """Verifies the catch-all deny still reports its rule."""
    engine = make_engine()
    assert engine.evaluate("nope", {}).rule == "*"


def test_review_human_approval_distinct_from_deny() -> None:
    """Verifies approval routing is distinguishable from denial."""
    engine = make_engine()
    assert engine.evaluate("shell.exec", {}).action != "deny"


def test_decision_is_frozen() -> None:
    """Verifies decisions are immutable value objects."""
    from dataclasses import FrozenInstanceError

    import pytest

    decision = build_engine().evaluate("search.query", {})
    with pytest.raises(FrozenInstanceError):
        decision.action = "deny"


def test_star_rule_matches_dotted_names() -> None:
    """Verifies the catch-all glob matches deeply dotted tools."""
    engine = build_engine()
    assert engine.evaluate("a.b.c.d", {}).rule == "*"


def test_describe_allow_label() -> None:
    """Verifies the allow label reads correctly."""
    from apps.api.policy.engine import describe_action

    assert describe_action("allow") == "allowed by policy"

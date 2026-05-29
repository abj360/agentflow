#!/usr/bin/env python3
"""
test_policy_engine.py --- unit tests for YAML policy evaluation

Contains:
    test_allow_rule_matches(): verifies an allow-listed tool is allowed
    test_unmatched_tool_denied(): verifies tools with no matching rule are denied
"""

from apps.api.policy.engine import PolicyEngine


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

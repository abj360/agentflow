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
            {"match": "*", "action": "deny"},
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

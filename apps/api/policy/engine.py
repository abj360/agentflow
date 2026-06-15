#!/usr/bin/env python3
"""
engine.py --- YAML policy engine for MCP tool governance

Contains:
    Decision: outcome of a policy evaluation
    CompiledRule: pre-compiled glob pattern plus its action
    PolicyEngine: evaluates tool calls against a compiled decision table
    is_allowed(): reports whether a decision permits the call
    describe_action(): renders an action as human-readable text
"""

import fnmatch
import re
from dataclasses import dataclass

import yaml


@dataclass(frozen=True)
class Decision:
    """Represents the outcome of a policy evaluation.

    Attributes:
        action: One of allow, deny, or human_approval.
        rule: The policy rule that produced the decision, if any matched.
        reason: Human-readable explanation of the decision.
    """

    action: str
    rule: str | None
    reason: str = ""


@dataclass(frozen=True)
class CompiledRule:
    """Holds a pre-compiled glob pattern plus its action.

    Attributes:
        pattern: Regex compiled from the rule's glob.
        action: Action the rule yields on a match.
        match: Original glob text for reporting.
    """

    pattern: re.Pattern
    action: str
    match: str


def _compile(rules: list[dict]) -> list[CompiledRule]:
    """Compiles raw policy rules into a decision table.

    Args:
        rules: Policy rules as plain dicts with match and action keys.

    Returns:
        table: Ordered compiled rules evaluated in sequence.
    """
    return [
        CompiledRule(
            pattern=re.compile(fnmatch.translate(rule["match"])),
            action=rule["action"],
            match=rule["match"],
        )
        for rule in rules
    ]


class PolicyEngine:
    """Evaluates tool calls against a compiled decision table.

    Attributes:
        schema_path: Path to the YAML policy schema, when file-backed.
    """

    def __init__(self, schema_path: str) -> None:
        """Initializes the engine and compiles the schema once.

        Args:
            schema_path: Path to the YAML policy schema.
        """
        self.schema_path = schema_path
        with open(schema_path) as handle:
            data = yaml.safe_load(handle)
        self._table = _compile(data["rules"])
        self._tenant_tables = {
            tenant: _compile(override.get("rules", []))
            for tenant, override in data.get("tenant_overrides", {}).items()
        }

    @classmethod
    def from_dict(cls, rules: list[dict]) -> "PolicyEngine":
        """Builds an engine from an in-memory rule list.

        Args:
            rules: Policy rules as plain dicts with match and action keys.

        Returns:
            engine: Policy engine evaluating the given rules.
        """
        engine = cls.__new__(cls)
        engine.schema_path = None
        engine._table = _compile(rules)
        engine._tenant_tables = {}
        return engine

    def evaluate(self, tool_name: str, args: dict, tenant_id: str | None = None) -> Decision:
        """Evaluates a tool call against the compiled decision table.

        Args:
            tool_name: Name of the tool being called.
            args: Arguments passed to the tool.
            tenant_id: Optional tenant whose override table applies first.

        Returns:
            decision: Allow, deny, or human_approval with the matched rule.
            Deny decisions carry a reason; allow decisions leave it empty.
        """
        table = self._table
        if tenant_id is not None and tenant_id in self._tenant_tables:
            table = self._tenant_tables[tenant_id]
        for rule in table:
            if rule.pattern.match(tool_name):
                return Decision(action=rule.action, rule=rule.match)
        return Decision(action="deny", rule=None, reason="no matching rule; default deny")


def is_allowed(decision: Decision) -> bool:
    """Reports whether a decision permits the call.

    Args:
        decision: The policy decision to inspect.

    Returns:
        allowed: True only for an explicit allow decision.
    """
    return decision.action == "allow"


def describe_action(action: str) -> str:
    """Renders an action as human-readable text.

    Args:
        action: The policy action to describe.

    Returns:
        description: Plain-language label for the action.
    """
    return {
        "allow": "allowed by policy",
        "deny": "denied by policy",
        "human_approval": "requires human approval",
    }.get(action, f"unknown action: {action}")

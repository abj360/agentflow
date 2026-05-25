#!/usr/bin/env python3
"""
engine.py --- YAML policy engine for MCP tool governance

Contains:
    Decision: outcome of a policy evaluation
    PolicyEngine: evaluates tool calls against YAML policy rules
"""

import fnmatch
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


class PolicyEngine:
    """Evaluates tool calls against YAML policy rules.

    Attributes:
        schema_path: Path to the YAML policy schema evaluated per call.
    """

    def __init__(self, schema_path: str) -> None:
        """Initializes the engine with a policy schema path.

        Args:
            schema_path: Path to the YAML policy schema evaluated per call.
        """
        self.schema_path = schema_path

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
        engine._inline_rules = rules
        return engine

    def _load_rules(self) -> list[dict]:
        """Loads the current rule set.

        Returns:
            rules: Policy rules as plain dicts.
        """
        if self.schema_path is None:
            return self._inline_rules
        with open(self.schema_path) as handle:
            return yaml.safe_load(handle)["rules"]

    def evaluate(
        self, tool_name: str, args: dict, tenant_id: str | None = None
    ) -> Decision:
        """Evaluates a tool call against the current policy rules.

        Args:
            tool_name: Name of the tool being called.
            args: Arguments passed to the tool.

        Returns:
            decision: Allow, deny, or human_approval with the matched rule.
        """
        rules = self._tenant_rules(tenant_id) if tenant_id else self._load_rules()
        for rule in rules:
            if fnmatch.fnmatchcase(tool_name, rule["match"]):
                return Decision(action=rule["action"], rule=rule["match"])
        return Decision(
            action="deny", rule=None, reason="no matching rule; default deny"
        )


    def _tenant_rules(self, tenant_id: str) -> list[dict]:
        """Loads tenant-specific override rules, falling back to base rules.

        Args:
            tenant_id: Tenant whose overrides apply.

        Returns:
            rules: The tenant's override rules, or the base rule set.
        """
        if self.schema_path is None:
            return self._inline_rules
        with open(self.schema_path) as handle:
            data = yaml.safe_load(handle)
        overrides = data.get("tenant_overrides", {})
        return overrides.get(tenant_id, {}).get("rules", data["rules"])


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

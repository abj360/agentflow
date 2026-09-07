#!/usr/bin/env python3
"""
conversations.py --- what has been said about each goal, for the coordinator

Contains:
    MAX_TURNS: how much of one conversation the coordinator is handed back
    Conversations: holds each run's conversation for the life of the process
    Conversations.append(): records one turn and returns the conversation
    Conversations.history(): returns a run's conversation, oldest turn first
    Conversations.forget(): drops a run's conversation
"""

from __future__ import annotations

from typing import Literal

from apps.api.orchestration.coordinator import Turn

MAX_TURNS = 40


class Conversations:
    """Holds each run's conversation for the life of the API process.

    The coordinator has to see the whole exchange to answer a follow-up about a
    plan it already built. This lives in memory rather than in the datastore
    because it is chat scrollback, not the audit record: the run's own history
    is hash-chained in the trace, and losing this on restart costs a reviewer a
    conversation, not evidence.

    Attributes:
        turns: Each run's conversation, keyed by run id.
    """

    def __init__(self, max_turns: int = MAX_TURNS) -> None:
        """Initializes an empty store.

        Args:
            max_turns: How many recent turns of a conversation are kept.
        """
        self.turns: dict[str, list[Turn]] = {}
        self._max_turns = max_turns

    def append(self, run_id: str, role: Literal["user", "assistant"], text: str) -> list[Turn]:
        """Records one turn and returns the conversation it belongs to.

        Args:
            run_id: Run the turn was said in.
            role: Who spoke.
            text: What was said.

        Returns:
            conversation: The run's turns, oldest first, capped to the recent ones.
        """
        conversation = self.turns.setdefault(run_id, [])
        conversation.append(Turn(role=role, text=text))
        del conversation[: max(0, len(conversation) - self._max_turns)]
        return list(conversation)

    def history(self, run_id: str) -> list[Turn]:
        """Returns a run's conversation, oldest turn first.

        Args:
            run_id: Run whose conversation is wanted.

        Returns:
            conversation: The turns said in that run, empty when there are none.
        """
        return list(self.turns.get(run_id, []))

    def forget(self, run_id: str) -> None:
        """Drops a run's conversation.

        Args:
            run_id: Run whose conversation is no longer needed.
        """
        self.turns.pop(run_id, None)

#!/usr/bin/env python3
"""
state.py --- immutable session state snapshots with optimistic concurrency

Contains:
    StateSnapshot: immutable point-in-time view of a session's agent state
    StateStore: atomically versions and stores session snapshots
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StateSnapshot:
    """Represents an immutable point-in-time view of a session's agent state.

    Attributes:
        session_id: Identifier of the session this snapshot belongs to.
        version: Monotonic version used for compare-and-swap updates.
        plan: Current plan steps as of this snapshot.
        results: Step outputs collected as of this snapshot.
    """

    session_id: str
    version: int
    plan: tuple[str, ...] = ()
    results: tuple[str, ...] = ()


class StateStore:
    """Atomically versions and stores session snapshots.

    Attributes:
        snapshots: Latest snapshot per session id.
    """

    def __init__(self) -> None:
        """Initializes the store with no sessions."""
        self._snapshots: dict[str, StateSnapshot] = {}

    def get(self, session_id: str) -> StateSnapshot:
        """Returns the latest snapshot for a session, creating an empty one.

        Args:
            session_id: Identifier of the session to look up.

        Returns:
            snapshot: Latest stored snapshot, or a version-zero empty one.
        """
        return self._snapshots.get(session_id, StateSnapshot(session_id, version=0))

    def compare_and_swap(self, expected_version: int, next_snapshot: StateSnapshot) -> bool:
        """Stores a new snapshot only if the expected version is current.

        Args:
            expected_version: Version the caller based its update on.
            next_snapshot: Snapshot to store when the version matches.

        Returns:
            swapped: True when stored, False on a version conflict.
        """
        current = self.get(next_snapshot.session_id)
        if current.version != expected_version:
            return False
        self._snapshots[next_snapshot.session_id] = next_snapshot
        return True

    def advance(
        self,
        session_id: str,
        *,
        plan: tuple[str, ...] | None = None,
        results: tuple[str, ...] | None = None,
    ) -> StateSnapshot:
        """Builds and stores the next snapshot for a session.

        Args:
            session_id: Session to advance.
            plan: Plan steps for the next snapshot, kept when omitted.
            results: Step outputs for the next snapshot, kept when omitted.

        Returns:
            snapshot: The newly stored snapshot with an incremented version.
        """
        current = self.get(session_id)
        next_snapshot = StateSnapshot(
            session_id=session_id,
            version=current.version + 1,
            plan=plan if plan is not None else current.plan,
            results=results if results is not None else current.results,
        )
        self._snapshots[session_id] = next_snapshot
        return next_snapshot

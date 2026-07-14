#!/usr/bin/env python3
"""
session.py --- versioned session records for the orchestration loop

Contains:
    SessionRecord: immutable record of a session's state at one version
    SessionRegistry: tracks sessions and their current version
    VersionConflictError: raised when a version bump loses a race
    SessionRegistry.open_session(): registers a new session at version zero
    SessionRegistry.bump_version(): increments a session's version
    SessionRegistry.close_session(): marks a session closed
    SessionRegistry.list_sessions(): lists all registered sessions
    SessionRegistry.expire_older_than(): removes idle sessions
"""

import time
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class SessionRecord:
    """Represents an immutable record of a session's state at one version.

    Attributes:
        session_id: Identifier of the orchestration session.
        version: Monotonic version incremented on every state transition.
        trace_id: Audit trace identifier linked to the session.
        created_at: Epoch seconds when the session was created.
    """

    session_id: str
    version: int
    trace_id: str
    created_at: float = field(default_factory=time.time)


class SessionRegistry:
    """Tracks sessions and their current version.

    Attributes:
        records: Latest record per session id.
    """

    def __init__(self) -> None:
        """Initializes the registry with no sessions."""
        self.records: dict[str, SessionRecord] = {}

    def open_session(
        self, session_id: str, trace_id: str, tenant_id: str = "default"
    ) -> SessionRecord:
        """Registers a new session at version zero.

        Args:
            session_id: Identifier of the session being opened.
            trace_id: Audit trace identifier linked to the session.

        Returns:
            record: The initial version-zero session record.
        """
        _ = tenant_id  # tenant lives on the audit row, not the version record
        record = SessionRecord(session_id=session_id, version=0, trace_id=trace_id)
        self.records[session_id] = record
        return record

    def bump_version(self, session_id: str) -> SessionRecord:
        """Increments a session's version and stores the new record.

        Args:
            session_id: Identifier of the session to advance.

        Returns:
            record: The session record carrying the incremented version.
        """
        if session_id not in self.records:
            raise KeyError(f"cannot bump unregistered session: {session_id}")
        current = self.records[session_id]
        updated = replace(current, version=current.version + 1)
        self.records[session_id] = updated
        return updated


class VersionConflictError(Exception):
    """Raised when a session version bump loses a concurrent race."""


    def close_session(self, session_id: str) -> SessionRecord:
        """Marks a session closed and returns its final record.

        Args:
            session_id: Identifier of the session being closed.

        Returns:
            record: The session's final record.
        """
        return self.records.pop(session_id)


    def list_sessions(self) -> list[SessionRecord]:
        """Lists all registered session records.

        Returns:
            records: Snapshot list of every registered session record.
        """
        return list(self.records.values())


    def expire_older_than(self, max_age_seconds: float) -> int:
        """Removes sessions idle longer than the given age.

        Args:
            max_age_seconds: Maximum idle age before a session expires.

        Returns:
            expired_count: Number of sessions removed.
        """
        cutoff = time.time() - max_age_seconds
        stale = [
            session_id
            for session_id, record in self.records.items()
            if record.created_at < cutoff
        ]
        for session_id in stale:
            del self.records[session_id]
        return len(stale)

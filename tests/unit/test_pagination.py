#!/usr/bin/env python3
"""
test_pagination.py --- unit tests for cursor pagination helpers

Contains:
    test_cursor_round_trip(): verifies an encoded cursor decodes to the same instant
    test_decode_cursor_rejects_garbage(): verifies malformed cursors raise a 400
"""

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from apps.api.audit.routes import MAX_PAGE_SIZE, decode_cursor, encode_cursor


def test_cursor_round_trip() -> None:
    """Verifies an encoded cursor decodes to the same instant."""
    stamp = datetime(2026, 6, 24, tzinfo=timezone.utc)
    assert decode_cursor(encode_cursor(stamp)) == stamp


def test_decode_cursor_rejects_garbage() -> None:
    """Verifies malformed cursors raise a 400."""
    with pytest.raises(HTTPException):
        decode_cursor("definitely-not-a-timestamp")

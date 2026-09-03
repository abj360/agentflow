#!/usr/bin/env python3
"""
test_pagination.py --- unit tests for cursor pagination helpers

Contains:
    test_cursor_round_trip(): verifies an encoded cursor decodes to the same instant
    test_decode_cursor_rejects_garbage(): verifies malformed cursors raise a 400
    test_encode_cursor_produces_iso_string(): verifies cursor encoding format
"""

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from apps.api.audit.routes import MAX_PAGE_SIZE, decode_cursor, encode_cursor


def test_cursor_round_trip() -> None:
    """Verifies an encoded cursor decodes to the same instant."""
    stamp = datetime(2026, 6, 24, tzinfo=UTC)
    assert decode_cursor(encode_cursor(stamp)) == stamp


def test_decode_cursor_rejects_garbage() -> None:
    """Verifies malformed cursors raise a 400."""
    with pytest.raises(HTTPException):
        decode_cursor("definitely-not-a-timestamp")


def test_encode_cursor_produces_iso_string() -> None:
    """Verifies the encoded cursor is an ISO-8601 timestamp string."""
    stamp = datetime(2026, 6, 24, 10, 15, tzinfo=UTC)
    assert encode_cursor(stamp).startswith("2026-06-24T10:15")


def test_decode_cursor_returns_datetime() -> None:
    """Verifies decoding yields a datetime for the WHERE clause comparison."""
    decoded = decode_cursor("2026-07-04T00:00:00+00:00")
    assert isinstance(decoded, datetime)


def test_encode_cursor_deterministic() -> None:
    """Verifies the same timestamp always encodes to the same token."""
    stamp = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
    assert encode_cursor(stamp) == encode_cursor(stamp)


def test_max_page_size_is_sane() -> None:
    """Verifies the page cap is positive and memory-safe."""
    assert 100 <= MAX_PAGE_SIZE <= 1000

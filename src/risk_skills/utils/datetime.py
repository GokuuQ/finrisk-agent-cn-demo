"""Datetime helpers."""

from datetime import datetime


def utc_now_iso():
    """Return an ISO-8601 UTC timestamp without requiring timezone objects."""

    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

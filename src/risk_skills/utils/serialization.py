"""Serialization helpers for metadata and config fingerprints."""

import hashlib
import json


def config_digest(config):
    """Return a stable digest for JSON-serializable config content."""

    try:
        payload = json.dumps(config or {}, ensure_ascii=False, sort_keys=True, default=str)
    except TypeError:
        payload = repr(config)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

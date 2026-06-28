"""Report naming helpers."""

from __future__ import absolute_import


def safe_sheet_name(name, existing=None):
    """Return an Excel-safe unique sheet name."""

    existing = set(existing or [])
    base = str(name).replace("/", "_").replace("\\", "_").replace("?", "_")
    base = base.replace("*", "_").replace("[", "_").replace("]", "_").replace(":", "_")
    base = base[:31] or "sheet"
    candidate = base
    idx = 1
    while candidate in existing:
        suffix = "_{0}".format(idx)
        candidate = base[: 31 - len(suffix)] + suffix
        idx += 1
    return candidate

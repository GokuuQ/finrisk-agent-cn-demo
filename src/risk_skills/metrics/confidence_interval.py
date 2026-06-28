"""Confidence interval helpers."""

from __future__ import absolute_import

import math


def wilson_interval(success_count, total_count, confidence=0.95):
    """Wilson interval for a binomial proportion."""

    if total_count <= 0:
        return {"low": float("nan"), "high": float("nan"), "proportion": float("nan")}
    z = _z_value(confidence)
    p = float(success_count) / float(total_count)
    denom = 1.0 + z * z / total_count
    center = (p + z * z / (2.0 * total_count)) / denom
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total_count)) / total_count) / denom
    return {
        "low": max(0.0, center - margin),
        "high": min(1.0, center + margin),
        "proportion": p,
    }


def _z_value(confidence):
    if confidence >= 0.995:
        return 2.807
    if confidence >= 0.99:
        return 2.576
    if confidence >= 0.95:
        return 1.96
    if confidence >= 0.90:
        return 1.645
    return 1.96

"""Lift and rule hit metrics."""

from __future__ import absolute_import

import math

import pandas as pd


def calc_lift(y_true, hit_mask, positive_value=1, smoothing=0.5):
    """Evaluate a boolean rule mask against a binary target."""

    data = pd.DataFrame({"y_true": y_true, "hit": hit_mask}).dropna(subset=["y_true"])
    if data.empty:
        return _empty_lift("Lift requires non-missing labels.")
    data["__rs_y"] = (data["y_true"] == positive_value).astype(int)
    data["hit"] = data["hit"].fillna(False).astype(bool)

    sample_count = int(len(data))
    bad_count = int(data["__rs_y"].sum())
    good_count = int(sample_count - bad_count)
    hit_count = int(data["hit"].sum())
    non_hit_count = int(sample_count - hit_count)
    hit_bad_count = int(data.loc[data["hit"], "__rs_y"].sum())
    non_hit_bad_count = int(bad_count - hit_bad_count)
    hit_good_count = int(hit_count - hit_bad_count)
    non_hit_good_count = int(good_count - hit_good_count)

    overall_bad_rate = _safe_div(bad_count, sample_count)
    hit_bad_rate = _safe_div(hit_bad_count, hit_count)
    non_hit_bad_rate = _safe_div(non_hit_bad_count, non_hit_count)
    lift = _safe_div(hit_bad_rate, overall_bad_rate)
    odds_ratio = ((hit_bad_count + smoothing) * (non_hit_good_count + smoothing)) / (
        (hit_good_count + smoothing) * (non_hit_bad_count + smoothing)
    )
    return {
        "sample_count": sample_count,
        "hit_count": hit_count,
        "hit_rate": _safe_div(hit_count, sample_count),
        "non_hit_count": non_hit_count,
        "bad_count": bad_count,
        "good_count": good_count,
        "hit_bad_count": hit_bad_count,
        "non_hit_bad_count": non_hit_bad_count,
        "overall_bad_rate": overall_bad_rate,
        "hit_bad_rate": hit_bad_rate,
        "non_hit_bad_rate": non_hit_bad_rate,
        "lift": lift,
        "bad_capture_rate": _safe_div(hit_bad_count, bad_count),
        "good_reject_rate": _safe_div(hit_good_count, good_count),
        "odds_ratio": float(odds_ratio),
        "warnings": [],
    }


def _empty_lift(warning):
    return {
        "sample_count": 0,
        "hit_count": 0,
        "hit_rate": float("nan"),
        "non_hit_count": 0,
        "bad_count": 0,
        "good_count": 0,
        "hit_bad_count": 0,
        "non_hit_bad_count": 0,
        "overall_bad_rate": float("nan"),
        "hit_bad_rate": float("nan"),
        "non_hit_bad_rate": float("nan"),
        "lift": float("nan"),
        "bad_capture_rate": float("nan"),
        "good_reject_rate": float("nan"),
        "odds_ratio": float("nan"),
        "warnings": [warning],
    }


def _safe_div(num, den):
    if den == 0 or pd.isna(den):
        return float("nan")
    return float(num) / float(den)

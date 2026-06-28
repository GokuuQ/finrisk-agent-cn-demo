"""Classification metrics used by risk analysis workflows."""

from __future__ import absolute_import

import math

import numpy as np
import pandas as pd


def _binary_frame(y_true, y_score=None, positive_value=1):
    data = pd.DataFrame({"y_true": y_true})
    if y_score is not None:
        data["y_score"] = y_score
        data = data.dropna(subset=["y_true", "y_score"])
    else:
        data = data.dropna(subset=["y_true"])
    data["__rs_y"] = (data["y_true"] == positive_value).astype(int)
    return data


def calc_auc(y_true, y_score, positive_value=1):
    """Calculate ROC AUC with a deterministic numpy fallback.

    Returns a structured dict and never flips scores when AUC is below 0.5.
    """

    data = _binary_frame(y_true, y_score, positive_value=positive_value)
    sample_count = int(len(data))
    bad_count = int(data["__rs_y"].sum())
    good_count = int(sample_count - bad_count)
    warnings = []
    if sample_count == 0 or bad_count == 0 or good_count == 0:
        warnings.append("AUC requires both positive and negative samples.")
        auc = float("nan")
    else:
        y = data["__rs_y"].to_numpy()
        score = data["y_score"].astype(float).to_numpy()
        auc = _auc_numpy(y, score)
    return {
        "auc": float(auc) if not pd.isna(auc) else float("nan"),
        "sample_count": sample_count,
        "bad_count": bad_count,
        "good_count": good_count,
        "warnings": warnings,
    }


def calc_ks(y_true, y_score, positive_value=1):
    """Calculate KS by sorting scores from high risk to low risk."""

    data = _binary_frame(y_true, y_score, positive_value=positive_value)
    sample_count = int(len(data))
    bad_count = int(data["__rs_y"].sum())
    good_count = int(sample_count - bad_count)
    warnings = []
    if sample_count == 0 or bad_count == 0 or good_count == 0:
        warnings.append("KS requires both positive and negative samples.")
        return {
            "ks": float("nan"),
            "threshold": None,
            "bad_cdf": float("nan"),
            "good_cdf": float("nan"),
            "sample_count": sample_count,
            "bad_count": bad_count,
            "good_count": good_count,
            "warnings": warnings,
        }

    ordered = data.sort_values("y_score", ascending=False, kind="mergesort")
    bad_cdf = ordered["__rs_y"].cumsum() / float(bad_count)
    good_cdf = (1 - ordered["__rs_y"]).cumsum() / float(good_count)
    diff = (bad_cdf - good_cdf).abs()
    pos = int(diff.to_numpy().argmax())
    return {
        "ks": float(diff.iloc[pos]),
        "threshold": ordered["y_score"].iloc[pos],
        "bad_cdf": float(bad_cdf.iloc[pos]),
        "good_cdf": float(good_cdf.iloc[pos]),
        "sample_count": sample_count,
        "bad_count": bad_count,
        "good_count": good_count,
        "warnings": warnings,
    }


def calc_brier_score(y_true, y_score, positive_value=1):
    """Calculate Brier score for probability-like predictions."""

    data = _binary_frame(y_true, y_score, positive_value=positive_value)
    sample_count = int(len(data))
    if sample_count == 0:
        return {
            "brier_score": float("nan"),
            "sample_count": 0,
            "warnings": ["Brier score requires non-missing labels and scores."],
        }
    y = data["__rs_y"].astype(float).to_numpy()
    score = data["y_score"].astype(float).to_numpy()
    return {
        "brier_score": float(np.mean((score - y) ** 2)),
        "sample_count": sample_count,
        "warnings": [],
    }


def _auc_numpy(y_true, y_score):
    ranks = _average_ranks(y_score)
    pos = y_true == 1
    n_pos = int(pos.sum())
    n_neg = int(len(y_true) - n_pos)
    rank_sum = float(ranks[pos].sum())
    return (rank_sum - n_pos * (n_pos + 1) / 2.0) / float(n_pos * n_neg)


def _average_ranks(values):
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    sorted_values = values[order]
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and sorted_values[end] == sorted_values[start]:
            end += 1
        avg_rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = avg_rank
        start = end
    return ranks

"""Data quality profiling helpers."""

from __future__ import absolute_import

import numpy as np
import pandas as pd


def profile_features(data, features):
    """Build a compact feature profile table for many columns."""

    rows = []
    row_count = int(len(data))
    for feature in features:
        series = data[feature]
        non_missing = series.dropna()
        unique_count = int(non_missing.nunique(dropna=True))
        row = {
            "feature": feature,
            "dtype": str(series.dtype),
            "row_count": row_count,
            "non_missing_count": int(non_missing.shape[0]),
            "coverage_rate": _safe_div(non_missing.shape[0], row_count),
            "missing_count": int(row_count - non_missing.shape[0]),
            "missing_rate": _safe_div(row_count - non_missing.shape[0], row_count),
            "unique_count": unique_count,
            "is_constant": unique_count <= 1,
            "top_value": None,
            "top_value_rate": float("nan"),
        }
        if not non_missing.empty:
            top_counts = non_missing.value_counts(dropna=True)
            row["top_value"] = str(top_counts.index[0])
            row["top_value_rate"] = _safe_div(int(top_counts.iloc[0]), row_count)
        if pd.api.types.is_numeric_dtype(series):
            numeric = pd.to_numeric(series, errors="coerce")
            row.update(_numeric_profile(numeric))
        rows.append(row)
    return pd.DataFrame(rows)


def _numeric_profile(series):
    quantiles = series.quantile([0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    return {
        "zero_rate": _safe_div(int((series == 0).sum()), int(len(series))),
        "mean": _float(series.mean()),
        "std": _float(series.std()),
        "min": _float(series.min()),
        "p01": _float(quantiles.loc[0.01]),
        "p05": _float(quantiles.loc[0.05]),
        "p10": _float(quantiles.loc[0.1]),
        "p25": _float(quantiles.loc[0.25]),
        "p50": _float(quantiles.loc[0.5]),
        "p75": _float(quantiles.loc[0.75]),
        "p90": _float(quantiles.loc[0.9]),
        "p95": _float(quantiles.loc[0.95]),
        "p99": _float(quantiles.loc[0.99]),
        "max": _float(series.max()),
    }


def _safe_div(num, den):
    if den == 0:
        return float("nan")
    return float(num) / float(den)


def _float(value):
    if pd.isna(value):
        return float("nan")
    return float(value)

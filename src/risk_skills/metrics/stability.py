"""Stability metrics such as PSI."""

from __future__ import absolute_import

import math

import pandas as pd


def calc_psi(expected_bins, actual_bins, smoothing=1e-6):
    """Calculate population stability index using common bin labels."""

    expected = pd.Series(expected_bins).fillna("99_MISSING").astype(str)
    actual = pd.Series(actual_bins).fillna("99_MISSING").astype(str)
    labels = sorted(set(expected.unique()).union(set(actual.unique())))
    exp_counts = expected.value_counts()
    act_counts = actual.value_counts()
    exp_total = float(len(expected))
    act_total = float(len(actual))
    rows = []
    for order, label in enumerate(labels, start=1):
        exp_pct = exp_counts.get(label, 0) / exp_total if exp_total else 0.0
        act_pct = act_counts.get(label, 0) / act_total if act_total else 0.0
        exp_s = max(exp_pct, smoothing)
        act_s = max(act_pct, smoothing)
        contribution = (act_s - exp_s) * math.log(act_s / exp_s)
        rows.append(
            {
                "bin_order": order,
                "bin_label": label,
                "expected_count": int(exp_counts.get(label, 0)),
                "actual_count": int(act_counts.get(label, 0)),
                "expected_pct": exp_pct,
                "actual_pct": act_pct,
                "psi_component": contribution,
            }
        )
    detail = pd.DataFrame(rows)
    psi = float(detail["psi_component"].sum()) if not detail.empty else float("nan")
    return {
        "psi": psi,
        "detail": detail,
        "expected_count": int(len(expected)),
        "actual_count": int(len(actual)),
        "warnings": [],
    }

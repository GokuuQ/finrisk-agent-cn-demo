"""Risk-specific WOE and IV metrics."""

from __future__ import absolute_import

import math

import numpy as np
import pandas as pd


def calc_woe_iv(y_true, bins, positive_value=1, smoothing=0.5):
    """Calculate WOE/IV for pre-computed bins."""

    data = pd.DataFrame({"y_true": y_true, "bin_label": bins}).dropna(subset=["y_true"])
    if data.empty:
        return {
            "detail": pd.DataFrame(),
            "total_iv": float("nan"),
            "sample_count": 0,
            "bad_count": 0,
            "good_count": 0,
            "warnings": ["IV requires non-missing labels."],
        }

    data["bin_label"] = data["bin_label"].fillna("99_MISSING").astype(str)
    data["__rs_y"] = (data["y_true"] == positive_value).astype(int)
    sample_count = int(len(data))
    total_bad = int(data["__rs_y"].sum())
    total_good = int(sample_count - total_bad)
    warnings = []
    if total_bad == 0 or total_good == 0:
        warnings.append("IV requires both positive and negative samples.")

    rows = []
    grouped = data.groupby("bin_label", sort=False, dropna=False)
    bin_count = max(1, grouped.ngroups)
    bad_den = total_bad + smoothing * bin_count
    good_den = total_good + smoothing * bin_count
    for order, (label, group) in enumerate(grouped, start=1):
        bad_count = int(group["__rs_y"].sum())
        sample = int(len(group))
        good_count = int(sample - bad_count)
        bad_dist = (bad_count + smoothing) / bad_den if bad_den else float("nan")
        good_dist = (good_count + smoothing) / good_den if good_den else float("nan")
        woe = math.log(bad_dist / good_dist) if bad_dist > 0 and good_dist > 0 else float("nan")
        iv_component = (bad_dist - good_dist) * woe if not pd.isna(woe) else float("nan")
        rows.append(
            {
                "bin_order": order,
                "bin_label": str(label),
                "sample_count": sample,
                "sample_rate": sample / float(sample_count),
                "bad_count": bad_count,
                "good_count": good_count,
                "bad_rate": bad_count / float(sample) if sample else float("nan"),
                "bad_distribution": bad_dist,
                "good_distribution": good_dist,
                "woe": woe,
                "iv_component": iv_component,
            }
        )

    detail = pd.DataFrame(rows)
    total_iv = float(detail["iv_component"].sum()) if not detail.empty else float("nan")
    detail["total_iv"] = total_iv
    return {
        "detail": detail,
        "total_iv": total_iv,
        "sample_count": sample_count,
        "bad_count": total_bad,
        "good_count": total_good,
        "warnings": warnings,
    }

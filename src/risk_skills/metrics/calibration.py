"""Calibration helpers."""

from __future__ import absolute_import

import pandas as pd

from risk_skills.binning.numeric import NumericBinner


def calibration_table(y_true, y_score, positive_value=1, bins=10):
    """Build a score-bin calibration table."""

    data = pd.DataFrame({"y_true": y_true, "score": y_score}).dropna(subset=["y_true", "score"])
    if data.empty:
        return pd.DataFrame()
    data["__rs_y"] = (data["y_true"] == positive_value).astype(int)
    binner = NumericBinner(n_bins=bins, method="quantile")
    bin_labels = binner.fit_transform(data["score"])
    data["bin_label"] = bin_labels
    rows = []
    for order, (label, group) in enumerate(data.groupby("bin_label", sort=False), start=1):
        rows.append(
            {
                "bin_order": order,
                "bin_label": label,
                "sample_count": int(len(group)),
                "prediction_mean": float(group["score"].mean()),
                "actual_bad_rate": float(group["__rs_y"].mean()),
            }
        )
    return pd.DataFrame(rows)

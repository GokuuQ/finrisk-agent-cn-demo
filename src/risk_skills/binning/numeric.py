"""Numeric binning with stable labels and no sample loss."""

from __future__ import absolute_import

import numpy as np
import pandas as pd

from risk_skills.binning.base import MISSING_LABEL, format_number
from risk_skills.core.exceptions import BinningError


class NumericBinner(object):
    """Fit numeric bins on reference data and transform later data."""

    def __init__(self, n_bins=10, method="quantile", manual_bins=None, special_values=None):
        self.n_bins = int(n_bins or 10)
        self.method = method or "quantile"
        self.manual_bins = manual_bins
        self.special_values = list(special_values or [])
        self.edges_ = None
        self.labels_ = None

    def fit(self, values):
        series = pd.Series(values)
        clean = pd.to_numeric(series[~series.isna() & ~series.isin(self.special_values)], errors="coerce")
        clean = clean.dropna()
        if clean.empty:
            self.edges_ = [float("-inf"), float("inf")]
            self.labels_ = ["01_[-inf, inf]"]
            return self

        if self.manual_bins is not None:
            internal = sorted(set(float(x) for x in self.manual_bins))
            edges = [float("-inf")] + internal + [float("inf")]
        elif self.method == "uniform":
            min_value = float(clean.min())
            max_value = float(clean.max())
            if min_value == max_value:
                edges = [float("-inf"), float("inf")]
            else:
                internal = np.linspace(min_value, max_value, self.n_bins + 1)[1:-1]
                edges = [float("-inf")] + sorted(set(float(x) for x in internal)) + [float("inf")]
        else:
            quantiles = np.linspace(0.0, 1.0, self.n_bins + 1)[1:-1]
            internal = clean.quantile(quantiles).drop_duplicates().tolist()
            edges = [float("-inf")] + sorted(set(float(x) for x in internal)) + [float("inf")]

        if len(edges) < 2:
            raise BinningError("numeric binning produced invalid edges")
        self.edges_ = edges
        self.labels_ = _labels_from_edges(edges)
        return self

    def transform(self, values):
        if self.edges_ is None:
            raise BinningError("NumericBinner must be fitted before transform")
        series = pd.Series(values)
        numeric = pd.to_numeric(series, errors="coerce")
        result = pd.Series(index=series.index, dtype=object)
        missing_mask = series.isna() | numeric.isna()
        special_mask = series.isin(self.special_values)
        regular_mask = ~missing_mask & ~special_mask

        if regular_mask.any():
            bin_index = np.searchsorted(np.asarray(self.edges_[1:-1]), numeric[regular_mask].to_numpy(), side="right")
            labels = [self.labels_[int(pos)] for pos in bin_index]
            result.loc[regular_mask] = labels
        result.loc[missing_mask] = MISSING_LABEL
        for value in self.special_values:
            mask = special_mask & (series == value)
            if mask.any():
                result.loc[mask] = "98_SPECIAL_{0}".format(format_number(value))
        return result.astype(str)

    def fit_transform(self, values):
        return self.fit(values).transform(values)


def _labels_from_edges(edges):
    labels = []
    last = len(edges) - 2
    for idx in range(len(edges) - 1):
        left = format_number(edges[idx])
        right = format_number(edges[idx + 1])
        if idx == last:
            label = "{0:02d}_[{1}, {2}]".format(idx + 1, left, right)
        else:
            label = "{0:02d}_[{1}, {2})".format(idx + 1, left, right)
        labels.append(label)
    return labels

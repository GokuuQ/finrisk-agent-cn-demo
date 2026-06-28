"""Categorical binning with rare category handling."""

from __future__ import absolute_import

import pandas as pd

from risk_skills.binning.base import MISSING_LABEL, OTHER_LABEL, safe_label
from risk_skills.core.exceptions import BinningError


class CategoricalBinner(object):
    """Fit frequent categories and collapse rare/unseen values to OTHER."""

    def __init__(self, max_levels=30, rare_rate=0.01):
        self.max_levels = int(max_levels or 30)
        self.rare_rate = float(rare_rate if rare_rate is not None else 0.01)
        self.categories_ = None
        self.category_to_label_ = None

    def fit(self, values):
        series = pd.Series(values)
        non_missing = series[~series.isna() & (series.astype(str) != "")]
        if non_missing.empty:
            self.categories_ = []
            self.category_to_label_ = {}
            return self
        counts = non_missing.astype(str).value_counts(dropna=False)
        total = float(len(non_missing))
        kept = []
        for value, count in counts.items():
            if len(kept) >= self.max_levels:
                break
            if count / total >= self.rare_rate:
                kept.append(str(value))
        self.categories_ = kept
        self.category_to_label_ = {
            value: "{0:02d}_{1}".format(idx + 1, safe_label(value))
            for idx, value in enumerate(self.categories_)
        }
        return self

    def transform(self, values):
        if self.category_to_label_ is None:
            raise BinningError("CategoricalBinner must be fitted before transform")
        series = pd.Series(values)
        result = pd.Series(index=series.index, dtype=object)
        missing_mask = series.isna() | (series.astype(str) == "")
        result.loc[missing_mask] = MISSING_LABEL
        text = series.astype(str)
        regular = ~missing_mask
        result.loc[regular] = text.loc[regular].map(self.category_to_label_).fillna(OTHER_LABEL)
        return result.astype(str)

    def fit_transform(self, values):
        return self.fit(values).transform(values)

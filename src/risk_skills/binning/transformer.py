"""Column-wise binning transformer."""

from __future__ import absolute_import

import pandas as pd

from risk_skills.binning.categorical import CategoricalBinner
from risk_skills.binning.numeric import NumericBinner


class BinTransformer(object):
    """Fit and reuse binning definitions for multiple DataFrame columns."""

    def __init__(
        self,
        numeric_features=None,
        categorical_features=None,
        manual_bins=None,
        special_values=None,
        n_bins=10,
        method="quantile",
        categorical_max_levels=30,
        rare_category_rate=0.01,
    ):
        self.numeric_features = set(numeric_features or [])
        self.categorical_features = set(categorical_features or [])
        self.manual_bins = dict(manual_bins or {})
        self.special_values = dict(special_values or {})
        self.n_bins = n_bins
        self.method = method
        self.categorical_max_levels = categorical_max_levels
        self.rare_category_rate = rare_category_rate
        self.binners_ = {}

    def fit(self, data, features):
        for feature in features:
            self.binners_[feature] = self._build_binner(data, feature).fit(data[feature])
        return self

    def transform(self, data):
        result = pd.DataFrame(index=data.index)
        for feature, binner in self.binners_.items():
            result[feature] = binner.transform(data[feature])
        return result

    def fit_transform(self, data, features):
        return self.fit(data, features).transform(data)

    def _build_binner(self, data, feature):
        if feature in self.categorical_features:
            return CategoricalBinner(
                max_levels=self.categorical_max_levels,
                rare_rate=self.rare_category_rate,
            )
        if feature in self.numeric_features or feature in self.manual_bins or _looks_numeric(data[feature]):
            return NumericBinner(
                n_bins=self.n_bins,
                method=self.method,
                manual_bins=self.manual_bins.get(feature),
                special_values=self.special_values.get(feature, []),
            )
        return CategoricalBinner(
            max_levels=self.categorical_max_levels,
            rare_rate=self.rare_category_rate,
        )


def _looks_numeric(series):
    if pd.api.types.is_numeric_dtype(series):
        return True
    converted = pd.to_numeric(series.dropna().head(200), errors="coerce")
    return len(converted) > 0 and converted.notna().mean() >= 0.9

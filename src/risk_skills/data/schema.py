"""Schema helpers for DataFrame-first workflows."""

from __future__ import absolute_import

import pandas as pd


def infer_features(data, config):
    """Infer feature columns from config and DataFrame columns."""

    data_cfg = config.get("data", {})
    feature_cfg = config.get("features", {})
    include = list(feature_cfg.get("include") or [])
    exclude = set(str(x) for x in feature_cfg.get("exclude") or [])

    protected = set()
    for key in ("id_col", "time_col", "split_col"):
        value = data_cfg.get(key)
        if value:
            protected.add(str(value))
    protected.update(str(x) for x in data_cfg.get("segment_cols") or [])
    raw_targets = config.get("targets") or []
    if isinstance(raw_targets, dict):
        raw_targets = [raw_targets]
    for target in raw_targets:
        if isinstance(target, dict):
            if target.get("target_col"):
                protected.add(str(target["target_col"]))
            if target.get("observe_col"):
                protected.add(str(target["observe_col"]))
    target = config.get("target") or {}
    if isinstance(target, dict):
        if target.get("target_col"):
            protected.add(str(target["target_col"]))
        if target.get("observe_col"):
            protected.add(str(target["observe_col"]))
    score = config.get("score") or {}
    if isinstance(score, dict) and score.get("score_col"):
        protected.add(str(score["score_col"]))

    if include:
        return [str(col) for col in include if str(col) in data.columns]
    return [str(col) for col in data.columns if str(col) not in protected and str(col) not in exclude]


def split_feature_types(data, features, config):
    """Split features into numeric and categorical lists."""

    feature_cfg = config.get("features", {})
    categorical = set(str(x) for x in feature_cfg.get("categorical") or [])
    numeric = set(str(x) for x in feature_cfg.get("numeric") or [])
    auto_numeric = []
    auto_categorical = []
    max_unique_as_category = int(feature_cfg.get("max_unique_as_category", 5))
    for feature in features:
        if feature in categorical:
            auto_categorical.append(feature)
        elif feature in numeric:
            auto_numeric.append(feature)
        elif pd.api.types.is_numeric_dtype(data[feature]) and data[feature].nunique(dropna=True) > max_unique_as_category:
            auto_numeric.append(feature)
        else:
            auto_categorical.append(feature)
    return auto_numeric, auto_categorical


def observed_target_frame(data, target_spec):
    """Return a target-valid copy for one target spec."""

    frame = data
    if target_spec.observe_col:
        frame = frame[frame[target_spec.observe_col] == 1]
    return frame.dropna(subset=[target_spec.target_col]).copy()

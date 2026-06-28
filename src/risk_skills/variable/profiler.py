"""Variable analysis helpers."""

from __future__ import absolute_import

import pandas as pd

from risk_skills.binning.transformer import BinTransformer
from risk_skills.data.quality import profile_features
from risk_skills.metrics import calc_auc, calc_ks, calc_lift, calc_woe_iv


def analyze_variables(data, features, targets, config):
    """Analyze many variables against one or more targets."""

    analysis_cfg = config.get("analysis", {})
    numeric_features = analysis_cfg.get("numeric_features") or []
    categorical_features = analysis_cfg.get("categorical_features") or []
    feature_cfg = config.get("features", {})
    transformer = BinTransformer(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        manual_bins=feature_cfg.get("manual_bins") or {},
        special_values=feature_cfg.get("special_values") or {},
        n_bins=analysis_cfg.get("numeric_bins", 10),
        categorical_max_levels=analysis_cfg.get("categorical_max_levels", 30),
        rare_category_rate=analysis_cfg.get("rare_category_rate", 0.01),
    )
    binned = transformer.fit_transform(data, features)
    profile = profile_features(data, features)
    summary_rows = []
    bin_tables = []
    warnings = []
    for target in targets:
        target_data = data
        target_bins = binned
        if target.observe_col:
            mask = data[target.observe_col] == 1
            target_data = data.loc[mask]
            target_bins = binned.loc[mask]
        target_data = target_data.dropna(subset=[target.target_col])
        target_bins = target_bins.loc[target_data.index]
        for feature in features:
            feature_bins = target_bins[feature]
            iv_result = calc_woe_iv(target_data[target.target_col], feature_bins, target.positive_value)
            detail = iv_result["detail"].copy()
            if not detail.empty:
                detail.insert(0, "feature", feature)
                detail.insert(1, "target", target.name)
                bin_tables.append(detail)
            score = _score_series(data.loc[target_data.index, feature])
            auc = calc_auc(target_data[target.target_col], score, target.positive_value)
            ks = calc_ks(target_data[target.target_col], score, target.positive_value)
            max_lift = _max_bin_lift(target_data[target.target_col], feature_bins, target.positive_value)
            warnings.extend(auc.get("warnings", []))
            warnings.extend(ks.get("warnings", []))
            warnings.extend(iv_result.get("warnings", []))
            summary_rows.append(
                {
                    "feature": feature,
                    "target": target.name,
                    "observed_count": int(len(target_data)),
                    "bad_count": int((target_data[target.target_col] == target.positive_value).sum()),
                    "good_count": int((target_data[target.target_col] != target.positive_value).sum()),
                    "bad_rate": _safe_mean(target_data[target.target_col] == target.positive_value),
                    "auc": auc["auc"],
                    "auc_strength": max(auc["auc"], 1 - auc["auc"]) if pd.notna(auc["auc"]) else float("nan"),
                    "ks": ks["ks"],
                    "iv": iv_result["total_iv"],
                    "max_bin_lift": max_lift,
                    "valid_bin_count": int(feature_bins.nunique(dropna=True)),
                    "rating": rate_variable(auc["auc"], ks["ks"], iv_result["total_iv"], profile, feature),
                }
            )
    bin_detail = pd.concat(bin_tables, ignore_index=True) if bin_tables else pd.DataFrame()
    return {
        "profile": profile,
        "summary": pd.DataFrame(summary_rows),
        "bin_detail": bin_detail,
        "binned": binned,
        "warnings": list(dict.fromkeys(str(w) for w in warnings if w)),
    }


def rate_variable(auc, ks, iv, profile, feature):
    row = profile.loc[profile["feature"] == feature]
    if not row.empty:
        if bool(row.iloc[0].get("is_constant", False)):
            return "D"
        if row.iloc[0].get("missing_rate", 0) > 0.95:
            return "D"
    strength = max(auc, 1 - auc) if pd.notna(auc) else float("nan")
    if pd.notna(strength) and strength >= 0.95:
        return "R"
    if (pd.notna(strength) and strength >= 0.62) or (pd.notna(ks) and ks >= 0.25) or (pd.notna(iv) and iv >= 0.2):
        return "A"
    if (pd.notna(strength) and strength >= 0.58) or (pd.notna(ks) and ks >= 0.15) or (pd.notna(iv) and iv >= 0.08):
        return "B"
    if (pd.notna(strength) and strength >= 0.53) or (pd.notna(iv) and iv >= 0.02):
        return "C"
    return "D"


def _score_series(series):
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    codes, _ = pd.factorize(series.fillna("__MISSING__").astype(str), sort=True)
    return pd.Series(codes, index=series.index)


def _max_bin_lift(y_true, bins, positive_value):
    best = float("nan")
    for label in pd.Series(bins).dropna().unique():
        lift = calc_lift(y_true, pd.Series(bins) == label, positive_value)
        value = lift.get("lift")
        if pd.notna(value) and (pd.isna(best) or value > best):
            best = value
    return best


def _safe_mean(values):
    values = pd.Series(values)
    if values.empty:
        return float("nan")
    return float(values.mean())

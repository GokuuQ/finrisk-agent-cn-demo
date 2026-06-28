"""Model score evaluation without model training dependencies."""

from __future__ import absolute_import

import pandas as pd

from risk_skills.binning.numeric import NumericBinner
from risk_skills.metrics import calc_auc, calc_brier_score, calc_ks, calc_lift, calc_psi
from risk_skills.metrics.calibration import calibration_table


def evaluate_score(data, target, score_col, config):
    """Evaluate an existing score/probability column."""

    score_cfg = config.get("score", {})
    bins = int(score_cfg.get("bins", 10))
    high_risk = bool(score_cfg.get("higher_score_higher_risk", True))
    frame = data
    if target.observe_col:
        frame = frame[frame[target.observe_col] == 1]
    frame = frame.dropna(subset=[target.target_col]).copy()
    raw_score = pd.to_numeric(frame[score_col], errors="coerce")
    missing_score_count = int(raw_score.isna().sum())
    frame = frame.loc[raw_score.notna()].copy()
    raw_score = raw_score.loc[frame.index]
    if not high_risk:
        score = -raw_score
        probability_score = 1.0 - raw_score
    else:
        score = raw_score
        probability_score = raw_score
    frame["__rs_score"] = score
    frame["__rs_prob"] = probability_score
    frame = frame.dropna(subset=["__rs_score"])

    overall = _overall_metrics(frame, target, score_col, missing_score_count)
    binner = NumericBinner(n_bins=bins, method="quantile")
    frame["score_bin"] = binner.fit_transform(frame["__rs_score"])
    score_bins = _score_bins(frame, target)
    period_metrics = _period_metrics(frame, target, config)
    segment_metrics = _segment_metrics(frame, target, config)
    split_metrics = _split_metrics(frame, target, config)
    calibration = calibration_table(frame[target.target_col], frame["__rs_prob"], target.positive_value, bins=bins)
    psi_detail = _psi_by_period(frame, config)
    stability = _stability_rating(overall, period_metrics, psi_detail)
    return {
        "overall_metrics": overall,
        "score_bins": score_bins,
        "period_metrics": period_metrics,
        "segment_metrics": segment_metrics,
        "split_metrics": split_metrics,
        "psi_detail": psi_detail,
        "calibration": calibration,
        "stability_summary": stability,
        "warnings": [],
    }


def _overall_metrics(frame, target, score_col, missing_score_count):
    auc = calc_auc(frame[target.target_col], frame["__rs_score"], target.positive_value)
    ks = calc_ks(frame[target.target_col], frame["__rs_score"], target.positive_value)
    if frame["__rs_prob"].between(0, 1).all():
        brier = calc_brier_score(frame[target.target_col], frame["__rs_prob"], target.positive_value)
        brier_score = brier["brier_score"]
    else:
        brier_score = float("nan")
    sample_count = int(len(frame))
    bad_count = int((frame[target.target_col] == target.positive_value).sum())
    return {
        "sample_count": sample_count,
        "bad_count": bad_count,
        "good_count": int(sample_count - bad_count),
        "bad_rate": bad_count / float(sample_count) if sample_count else float("nan"),
        "auc": auc["auc"],
        "ks": ks["ks"],
        "gini": 2 * auc["auc"] - 1 if pd.notna(auc["auc"]) else float("nan"),
        "brier_score": brier_score,
        "score_mean": float(frame["__rs_score"].mean()) if sample_count else float("nan"),
        "score_std": float(frame["__rs_score"].std()) if sample_count else float("nan"),
        "score_min": float(frame["__rs_score"].min()) if sample_count else float("nan"),
        "score_max": float(frame["__rs_score"].max()) if sample_count else float("nan"),
        "missing_score_count": missing_score_count,
    }


def _score_bins(frame, target):
    rows = []
    for order, (label, group) in enumerate(frame.groupby("score_bin", sort=False), start=1):
        lift = calc_lift(frame[target.target_col], frame["score_bin"] == label, target.positive_value)
        bad_count = int((group[target.target_col] == target.positive_value).sum())
        rows.append(
            {
                "bin_order": order,
                "bin_label": label,
                "score_min": float(group["__rs_score"].min()),
                "score_max": float(group["__rs_score"].max()),
                "sample_count": int(len(group)),
                "sample_rate": len(group) / float(len(frame)) if len(frame) else float("nan"),
                "bad_count": bad_count,
                "good_count": int(len(group) - bad_count),
                "bad_rate": bad_count / float(len(group)) if len(group) else float("nan"),
                "lift": lift["lift"],
                "bad_capture_rate": lift["bad_capture_rate"],
            }
        )
    return pd.DataFrame(rows)


def _period_metrics(frame, target, config):
    time_col = config.get("data", {}).get("time_col")
    if not time_col or time_col not in frame.columns:
        return pd.DataFrame()
    rows = []
    for period, group in frame.groupby(time_col, sort=True):
        rows.append(_group_metrics(group, target, {"period": period}))
    return pd.DataFrame(rows)


def _segment_metrics(frame, target, config):
    segment_cols = config.get("data", {}).get("segment_cols") or []
    rows = []
    for col in segment_cols:
        if col not in frame.columns:
            continue
        for value, group in frame.groupby(col, sort=False):
            rows.append(_group_metrics(group, target, {"segment_name": col, "segment_value": value}))
    return pd.DataFrame(rows)


def _split_metrics(frame, target, config):
    split_col = config.get("data", {}).get("split_col")
    if not split_col or split_col not in frame.columns:
        return pd.DataFrame()
    rows = []
    for value, group in frame.groupby(split_col, sort=False):
        rows.append(_group_metrics(group, target, {"split": value}))
    return pd.DataFrame(rows)


def _group_metrics(group, target, extra):
    auc = calc_auc(group[target.target_col], group["__rs_score"], target.positive_value)
    ks = calc_ks(group[target.target_col], group["__rs_score"], target.positive_value)
    bad_count = int((group[target.target_col] == target.positive_value).sum())
    row = {
        "sample_count": int(len(group)),
        "bad_count": bad_count,
        "bad_rate": bad_count / float(len(group)) if len(group) else float("nan"),
        "auc": auc["auc"],
        "ks": ks["ks"],
        "score_mean": float(group["__rs_score"].mean()) if len(group) else float("nan"),
        "score_std": float(group["__rs_score"].std()) if len(group) else float("nan"),
    }
    row.update(extra)
    return row


def _psi_by_period(frame, config):
    time_col = config.get("data", {}).get("time_col")
    if not time_col or time_col not in frame.columns:
        return pd.DataFrame()
    periods = sorted(frame[time_col].dropna().unique())
    if len(periods) < 2:
        return pd.DataFrame()
    expected = frame.loc[frame[time_col] == periods[0], "score_bin"]
    rows = []
    for period in periods[1:]:
        psi = calc_psi(expected, frame.loc[frame[time_col] == period, "score_bin"])
        rows.append({"period": period, "psi": psi["psi"], "expected_period": periods[0]})
    return pd.DataFrame(rows)


def _stability_rating(overall, period_metrics, psi_detail):
    rating = "STABLE"
    reasons = []
    if overall.get("sample_count", 0) == 0 or pd.isna(overall.get("auc")):
        rating = "INVALID"
        reasons.append("insufficient valid score samples")
    elif overall.get("auc", 0) < 0.55 or overall.get("ks", 0) < 0.1:
        rating = "WATCH"
        reasons.append("weak overall discrimination")
    if not psi_detail.empty and psi_detail["psi"].max() > 0.25:
        rating = "UNSTABLE"
        reasons.append("score PSI exceeds 0.25")
    elif not psi_detail.empty and psi_detail["psi"].max() > 0.1 and rating == "STABLE":
        rating = "WATCH"
        reasons.append("score PSI exceeds 0.10")
    return {"rating": rating, "reasons": reasons}

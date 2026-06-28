"""Candidate rule mining with bounded search."""

from __future__ import absolute_import

import itertools

import pandas as pd

from risk_skills.metrics import calc_lift
from risk_skills.strategy.rule import CompositeRule, Rule


def mine_rules(data, features, target, numeric_features, categorical_features, config):
    """Mine single-variable and optional pairwise-AND rules."""

    mining = config.get("mining", {})
    max_candidates_per_feature = int(mining.get("max_candidates_per_feature", 8))
    max_hit_rate = float(mining.get("max_hit_rate", 0.5))
    min_hit_rate = float(mining.get("min_hit_rate", 0.01))
    min_lift = float(mining.get("min_lift", 1.1))
    top_for_combine = int(mining.get("top_single_rules_for_combine", 20))
    enable_pairwise = bool(mining.get("enable_pairwise_and", True))

    target_data = data
    if target.observe_col:
        target_data = data[data[target.observe_col] == 1]
    target_data = target_data.dropna(subset=[target.target_col])

    candidate_rules = []
    for feature in features:
        if feature in numeric_features:
            candidate_rules.extend(_numeric_rules(target_data, feature, max_candidates_per_feature))
        else:
            candidate_rules.extend(_categorical_rules(target_data, feature, max_candidates_per_feature))
        if target_data[feature].isna().any():
            candidate_rules.append(Rule("R{0:05d}".format(len(candidate_rules) + 1), feature, "missing"))

    evaluated = []
    for idx, rule in enumerate(candidate_rules, start=1):
        rule.rule_id = "R{0:05d}".format(idx)
        row = evaluate_rule(target_data, rule, target)
        if row["hit_rate"] >= min_hit_rate and row["hit_rate"] <= max_hit_rate and row["lift"] >= min_lift:
            evaluated.append(row)

    single = pd.DataFrame(evaluated)
    if not single.empty:
        single = single.sort_values(["lift", "bad_capture_rate", "hit_count"], ascending=[False, False, False])

    composite_rows = []
    if enable_pairwise and not single.empty:
        top_ids = single.head(top_for_combine)["rule_object"].tolist()
        for a, b in itertools.combinations(top_ids, 2):
            if a.feature == b.feature:
                continue
            comp = CompositeRule("C{0:05d}".format(len(composite_rows) + 1), [a, b])
            row = evaluate_rule(target_data, comp, target)
            if row["hit_rate"] >= min_hit_rate and row["hit_rate"] <= max_hit_rate and row["lift"] >= min_lift:
                composite_rows.append(row)
    composite = pd.DataFrame(composite_rows)
    if not composite.empty:
        composite = composite.sort_values(["lift", "bad_capture_rate", "hit_count"], ascending=[False, False, False])
    return single, composite


def evaluate_rule(data, rule, target):
    mask = rule.evaluate(data)
    metrics = calc_lift(data[target.target_col], mask, target.positive_value)
    return dict(
        {
            "rule_id": rule.rule_id,
            "rule_expression": rule.label(),
            "feature_count": len(getattr(rule, "rules", [])) or 1,
            "target": target.name,
            "python_expression": rule.to_python(),
            "sql_expression": rule.to_sql(),
            "rule_object": rule,
        },
        **metrics
    )


def _numeric_rules(data, feature, max_candidates):
    series = pd.to_numeric(data[feature], errors="coerce").dropna()
    if series.empty:
        return []
    quantiles = series.quantile([0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9]).drop_duplicates().tolist()
    values = sorted(set(float(x) for x in quantiles))[:max_candidates]
    rules = []
    for threshold in values:
        rules.append(Rule("", feature, ">=", threshold=threshold))
        rules.append(Rule("", feature, "<=", threshold=threshold))
    return rules[: max_candidates * 2]


def _categorical_rules(data, feature, max_candidates):
    counts = data[feature].dropna().astype(str).value_counts().head(max_candidates)
    return [Rule("", feature, "in", values=[value]) for value in counts.index.tolist()]

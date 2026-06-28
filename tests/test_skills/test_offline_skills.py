from __future__ import annotations

from risk_skills.skills import ModelEvaluationSkill, RuleMiningSkill, VariableAnalysisSkill


def test_variable_analysis_handles_wide_frame_without_export(wide_risk_frame) -> None:
    config = {
        "data": {"id_col": "cust_id", "time_col": "loan_month", "segment_cols": ["channel"]},
        "targets": [{"name": "fpd7", "target_col": "fpd7", "observe_col": "can_7"}],
        "features": {
            "include": ["query_count_30d", "credit_score", "device_risk"] + ["noise_%03d" % i for i in range(20)],
            "categorical": ["device_risk"],
        },
        "analysis": {"numeric_bins": 5, "max_features": 50},
        "output": {"enabled": False},
    }

    result = VariableAnalysisSkill(config=config).run(wide_risk_frame)

    assert result.status == "success"
    assert result.details["feature_count"] == 23
    assert not result.summary.empty
    assert {"feature", "target", "auc", "ks", "iv", "rating"}.issubset(result.summary.columns)


def test_rule_mining_finds_candidates_without_export(wide_risk_frame) -> None:
    config = {
        "data": {"time_col": "loan_month", "split_col": "split"},
        "targets": [{"name": "fpd7", "target_col": "fpd7", "observe_col": "can_7"}],
        "features": {
            "include": ["query_count_30d", "credit_score", "device_risk"],
            "categorical": ["device_risk"],
        },
        "mining": {
            "min_hit_rate": 0.02,
            "max_hit_rate": 0.60,
            "min_lift": 1.05,
            "max_candidates_per_feature": 6,
            "enable_pairwise_and": True,
        },
        "output": {"enabled": False},
    }

    result = RuleMiningSkill(config=config).run(wide_risk_frame)

    assert result.status == "success"
    assert not result.details["single_rule_detail"].empty
    assert "python_expression" in result.details["single_rule_detail"].columns
    assert "sql_expression" in result.details["single_rule_detail"].columns


def test_model_evaluation_uses_existing_score_without_export(wide_risk_frame) -> None:
    config = {
        "data": {"time_col": "loan_month", "segment_cols": ["channel"], "split_col": "split"},
        "target": {"name": "fpd7", "target_col": "fpd7", "observe_col": "can_7"},
        "score": {"score_col": "model_score", "higher_score_higher_risk": True, "bins": 5},
        "output": {"enabled": False},
    }

    result = ModelEvaluationSkill(config=config).run(wide_risk_frame)

    assert result.status == "success"
    assert result.summary["sample_count"] == len(wide_risk_frame)
    assert result.summary["auc"] > 0.6
    assert not result.details["score_bins"].empty
    assert result.details["stability_summary"]["rating"] in {"STABLE", "WATCH", "UNSTABLE", "INVALID"}

from __future__ import annotations

import json

import pytest

from risk_skills.core.config import (
    FeatureSpec,
    TargetSpec,
    build_feature_specs,
    build_target_specs,
    load_config,
)
from risk_skills.core.exceptions import ConfigError


def test_load_config_merges_defaults_file_and_explicit_dict(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "analysis": {"bins": 5, "calculate_auc": False},
                "output": {"enabled": True},
            }
        ),
        encoding="utf-8",
    )

    config = load_config(
        path=config_path,
        defaults={"analysis": {"bins": 10}, "runtime": {"random_state": 7}},
        config={"analysis": {"calculate_auc": True}},
    )

    assert config["analysis"]["bins"] == 5
    assert config["analysis"]["calculate_auc"] is True
    assert config["output"]["enabled"] is True
    assert config["runtime"]["random_state"] == 7


def test_load_config_rejects_unknown_file_type(tmp_path) -> None:
    config_path = tmp_path / "config.txt"
    config_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(path=config_path)


def test_build_target_specs_accepts_mapping_and_list() -> None:
    targets = build_target_specs(
        [
            {
                "name": "fpd7",
                "target_col": "fpd7",
                "observe_col": "can_7",
                "positive_value": 1,
            }
        ]
    )

    assert targets == [
        TargetSpec(
            name="fpd7",
            target_col="fpd7",
            observe_col="can_7",
            positive_value=1,
            task_type="risk",
            description=None,
        )
    ]


def test_build_feature_specs_accepts_names_and_mappings() -> None:
    features = build_feature_specs(
        [
            "query_count_30d",
            {"name": "credit_score", "feature_type": "numeric", "direction": -1},
        ]
    )

    assert features == [
        FeatureSpec(name="query_count_30d"),
        FeatureSpec(name="credit_score", feature_type="numeric", direction=-1),
    ]

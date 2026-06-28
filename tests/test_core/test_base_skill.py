from __future__ import annotations

import pytest

from risk_skills.core import BaseRiskSkill, InputValidationError, RiskSkillsError, SkillResult
from risk_skills.core.validation import require_dataframe_like


class DummyData:
    columns = ["feature", "target"]
    shape = (3, 2)


class DummySkill(BaseRiskSkill):
    skill_name = "dummy"
    skill_version = "0.1.0"

    def validate_input(self, data):
        require_dataframe_like(data, skill_name=self.skill_name)

    def prepare_data(self, data):
        self.events = ["prepare_data"]
        return data

    def run_analysis(self, data):
        self.events.append("run_analysis")
        result = SkillResult(
            status="success",
            details={"row_count": data.shape[0]},
            warnings=["analysis warning"],
        )
        return result

    def validate_result(self, result):
        self.events.append("validate_result")
        assert result.details["row_count"] == 3

    def generate_summary(self, result):
        self.events.append("generate_summary")
        return {"rows": result.details["row_count"]}

    def export(self, result):
        self.events.append("export")
        return {"dummy": "memory://dummy"}


class FailingSkill(DummySkill):
    skill_name = "failing_dummy"

    def run_analysis(self, data):
        raise ValueError("boom")


def test_base_skill_runs_lifecycle_and_metadata() -> None:
    skill = DummySkill(
        config={
            "output": {"enabled": True, "directory": "output/tests"},
            "runtime": {"random_state": 42},
        }
    )

    result = skill.run(DummyData())

    assert result.status == "success"
    assert result.summary == {"rows": 3}
    assert result.exports == {"dummy": "memory://dummy"}
    assert result.warnings == ["analysis warning"]
    assert result.metadata["skill_name"] == "dummy"
    assert result.metadata["row_count"] == 3
    assert result.metadata["column_count"] == 2
    assert result.metadata["random_state"] == 42
    assert result.metadata["config_digest"]
    assert skill.result is result
    assert skill.events == [
        "prepare_data",
        "run_analysis",
        "validate_result",
        "generate_summary",
        "export",
    ]


def test_base_skill_can_disable_export() -> None:
    skill = DummySkill(config={"output": {"enabled": False}})

    result = skill.run(DummyData())

    assert result.exports == {}
    assert "export" not in skill.events


def test_base_skill_wraps_unexpected_errors_with_stage() -> None:
    skill = FailingSkill()

    with pytest.raises(RiskSkillsError, match=r"skill=failing_dummy.*stage=run_analysis"):
        skill.run(DummyData())


def test_dataframe_like_validation_error_is_clear() -> None:
    skill = DummySkill()

    with pytest.raises(InputValidationError, match="DataFrame-like"):
        skill.run(object())

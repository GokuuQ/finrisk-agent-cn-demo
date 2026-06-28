"""RuleMiningSkill: bounded offline rule discovery."""

from __future__ import absolute_import

from pathlib import Path

from risk_skills.core import BaseRiskSkill, InputValidationError, SkillResult
from risk_skills.core.config import build_target_specs
from risk_skills.core.validation import require_columns, require_dataframe_like
from risk_skills.data import infer_features, split_feature_types
from risk_skills.report import write_excel_report, write_markdown_report
from risk_skills.strategy.miner import mine_rules


class RuleMiningSkill(BaseRiskSkill):
    """Mine interpretable single-variable and pairwise AND risk rules."""

    skill_name = "rule_mining"
    skill_version = "0.1.0"

    def validate_input(self, data):
        require_dataframe_like(data, skill_name=self.skill_name)
        if len(data) == 0:
            raise InputValidationError("input data is empty", skill_name=self.skill_name)
        targets = build_target_specs(self.config.get("targets"))
        if not targets:
            raise InputValidationError("at least one target is required", skill_name=self.skill_name)
        cols = []
        for target in targets:
            cols.append(target.target_col)
            if target.observe_col:
                cols.append(target.observe_col)
        require_columns(data, cols, skill_name=self.skill_name)

    def run_analysis(self, data):
        targets = build_target_specs(self.config.get("targets"))
        features = infer_features(data, self.config)
        max_features = int(self.config.get("mining", {}).get("max_features", 200))
        if len(features) > max_features:
            self.add_warning("feature count {0} exceeds max_features {1}; truncated.".format(len(features), max_features))
            features = features[:max_features]
        numeric, categorical = split_feature_types(data, features, self.config)
        singles = []
        composites = []
        for target in targets:
            single, composite = mine_rules(data, features, target, numeric, categorical, self.config)
            if not single.empty:
                singles.append(single.drop(columns=["rule_object"]))
            if not composite.empty:
                composites.append(composite.drop(columns=["rule_object"]))
        single_detail = _concat(singles)
        composite_detail = _concat(composites)
        return SkillResult(
            status="success",
            summary=single_detail.head(50),
            details={
                "single_rule_detail": single_detail,
                "composite_rule_detail": composite_detail,
                "feature_count": len(features),
            },
            warnings=self.warnings,
        )

    def export(self, result):
        output_dir = Path(self.output_dir or self.config.get("output", {}).get("directory", "output/rule_mining"))
        output_dir.mkdir(parents=True, exist_ok=True)
        exports = {}
        if self.config.get("output", {}).get("excel", True):
            exports["excel"] = write_excel_report(
                output_dir / "rule_mining.xlsx",
                {
                    "00_run_info": result.metadata,
                    "01_single_rule_detail": result.details["single_rule_detail"],
                    "02_composite_rule_detail": result.details["composite_rule_detail"],
                },
            )
        if self.config.get("output", {}).get("markdown", True):
            exports["markdown"] = write_markdown_report(
                output_dir / "rule_mining.md",
                "规则挖掘报告",
                [
                    "完成 {0} 个变量的候选规则挖掘。".format(result.details["feature_count"]),
                    "单变量达标规则数：{0}。".format(len(result.details["single_rule_detail"])),
                    "双变量组合达标规则数：{0}。".format(len(result.details["composite_rule_detail"])),
                ],
                metadata=result.metadata,
                warnings=result.warnings,
            )
        return exports


def _concat(frames):
    import pandas as pd

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

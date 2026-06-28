"""VariableAnalysisSkill: wide-table variable diagnostics."""

from __future__ import absolute_import

from pathlib import Path

from risk_skills.core import BaseRiskSkill, InputValidationError, SkillResult
from risk_skills.core.config import build_target_specs
from risk_skills.core.validation import require_columns, require_dataframe_like
from risk_skills.data import infer_features, split_feature_types
from risk_skills.report import write_excel_report, write_markdown_report
from risk_skills.variable.profiler import analyze_variables


class VariableAnalysisSkill(BaseRiskSkill):
    """Offline variable diagnostics for many columns and one or more labels."""

    skill_name = "variable_analysis"
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
        max_features = int(self.config.get("analysis", {}).get("max_features", 300))
        if len(features) > max_features:
            self.add_warning("feature count {0} exceeds max_features {1}; truncated.".format(len(features), max_features))
            features = features[:max_features]
        numeric, categorical = split_feature_types(data, features, self.config)
        analysis_config = dict(self.config)
        analysis_config.setdefault("analysis", {})
        analysis_config["analysis"]["numeric_features"] = numeric
        analysis_config["analysis"]["categorical_features"] = categorical
        result = analyze_variables(data, features, targets, analysis_config)
        warnings = self.warnings + result["warnings"]
        return SkillResult(
            status="success",
            summary=result["summary"],
            details={
                "feature_profile": result["profile"],
                "feature_summary": result["summary"],
                "bin_detail": result["bin_detail"],
                "feature_count": len(features),
                "numeric_feature_count": len(numeric),
                "categorical_feature_count": len(categorical),
            },
            warnings=list(dict.fromkeys(warnings)),
        )

    def export(self, result):
        output_dir = Path(self.output_dir or self.config.get("output", {}).get("directory", "output/variable_analysis"))
        output_dir.mkdir(parents=True, exist_ok=True)
        exports = {}
        if self.config.get("output", {}).get("excel", True):
            exports["excel"] = write_excel_report(
                output_dir / "variable_analysis.xlsx",
                {
                    "00_run_info": result.metadata,
                    "01_feature_profile": result.details["feature_profile"],
                    "02_feature_summary": result.details["feature_summary"],
                    "03_bin_detail": result.details["bin_detail"],
                },
            )
        if self.config.get("output", {}).get("markdown", True):
            summary = result.summary
            lines = [
                "完成 {0} 个变量的离线诊断。".format(result.details["feature_count"]),
                "A/B 类变量数量：{0}。".format(int(summary["rating"].isin(["A", "B"]).sum()) if not summary.empty else 0),
            ]
            exports["markdown"] = write_markdown_report(
                output_dir / "variable_analysis.md",
                "变量分析报告",
                lines,
                metadata=result.metadata,
                warnings=result.warnings,
            )
        return exports

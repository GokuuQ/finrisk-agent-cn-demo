"""ModelEvaluationSkill: evaluate existing model scores."""

from __future__ import absolute_import

from pathlib import Path

from risk_skills.core import BaseRiskSkill, InputValidationError, SkillResult, TargetSpec
from risk_skills.core.validation import require_columns, require_dataframe_like
from risk_skills.model.score_evaluator import evaluate_score
from risk_skills.report import write_excel_report, write_markdown_report


class ModelEvaluationSkill(BaseRiskSkill):
    """Evaluate an existing score/probability column without training packages."""

    skill_name = "model_evaluation"
    skill_version = "0.1.0"

    def validate_input(self, data):
        require_dataframe_like(data, skill_name=self.skill_name)
        if len(data) == 0:
            raise InputValidationError("input data is empty", skill_name=self.skill_name)
        target = self._target_spec()
        score_col = self._score_col()
        cols = [target.target_col, score_col]
        if target.observe_col:
            cols.append(target.observe_col)
        require_columns(data, cols, skill_name=self.skill_name)

    def run_analysis(self, data):
        target = self._target_spec()
        score_col = self._score_col()
        result = evaluate_score(data, target, score_col, self.config)
        return SkillResult(
            status="success",
            summary=result["overall_metrics"],
            details=result,
            warnings=result["warnings"],
            recommendations=[result["stability_summary"]],
        )

    def export(self, result):
        output_dir = Path(self.output_dir or self.config.get("output", {}).get("directory", "output/model_evaluation"))
        output_dir.mkdir(parents=True, exist_ok=True)
        exports = {}
        if self.config.get("output", {}).get("excel", True):
            exports["excel"] = write_excel_report(
                output_dir / "model_evaluation.xlsx",
                {
                    "00_run_info": result.metadata,
                    "01_overall_metrics": result.details["overall_metrics"],
                    "02_score_bins": result.details["score_bins"],
                    "03_period_metrics": result.details["period_metrics"],
                    "04_segment_metrics": result.details["segment_metrics"],
                    "05_split_metrics": result.details["split_metrics"],
                    "06_psi_detail": result.details["psi_detail"],
                    "07_calibration": result.details["calibration"],
                    "08_stability_summary": result.details["stability_summary"],
                },
            )
        if self.config.get("output", {}).get("markdown", True):
            summary = result.summary
            exports["markdown"] = write_markdown_report(
                output_dir / "model_evaluation.md",
                "模型评分评估报告",
                [
                    "样本数：{0}，坏样本率：{1:.2%}。".format(summary["sample_count"], summary["bad_rate"]),
                    "AUC：{0:.4f}，KS：{1:.4f}。".format(summary["auc"], summary["ks"]),
                    "稳定性评级：{0}。".format(result.details["stability_summary"]["rating"]),
                ],
                metadata=result.metadata,
                warnings=result.warnings,
            )
        return exports

    def _target_spec(self):
        target = self.config.get("target")
        if not isinstance(target, dict):
            raise InputValidationError("target config is required", skill_name=self.skill_name)
        return TargetSpec(**target)

    def _score_col(self):
        score = self.config.get("score") or {}
        score_col = score.get("score_col")
        if not score_col:
            raise InputValidationError("score.score_col is required", skill_name=self.skill_name)
        return score_col

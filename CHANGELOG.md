# Changelog

## 0.1.0 - 2026-06-28

- Initialized the `risk_skills` package skeleton.
- Added core exceptions, result dataclasses, configuration loading, logging helpers, and the base Skill lifecycle.
- Added Phase 0 tests for importability, config loading, and unified Skill execution.
- Added offline metric functions for AUC, KS, IV/WOE, Lift, PSI, Brier score, calibration, and Wilson intervals.
- Added numeric/categorical binning and a reusable `BinTransformer`.
- Added MVP `VariableAnalysisSkill`, `RuleMiningSkill`, and `ModelEvaluationSkill` implementations for DataFrame-first workflows.
- Added compact Excel and Markdown exporters.
- Added reproducible wide-table demo scripts and tests for metrics, binning, and the three Skills.

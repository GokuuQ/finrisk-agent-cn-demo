from __future__ import absolute_import

import pandas as pd

from risk_skills.skills import ModelEvaluationSkill


def main():
    df = pd.read_csv("data/risk_skills_demo.csv")
    config = {
        "data": {"time_col": "loan_month", "segment_cols": ["channel"], "split_col": "split"},
        "target": {"name": "fpd7", "target_col": "fpd7", "observe_col": "can_7"},
        "score": {"score_col": "model_score", "higher_score_higher_risk": True, "bins": 10},
        "output": {"enabled": True, "directory": "output/model_evaluation", "excel": True, "markdown": True},
    }
    result = ModelEvaluationSkill(config=config).run(df)
    print(result.summary)
    print(result.exports)


if __name__ == "__main__":
    main()

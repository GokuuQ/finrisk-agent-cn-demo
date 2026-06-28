from __future__ import absolute_import

import pandas as pd

from risk_skills.skills import VariableAnalysisSkill


def main():
    df = pd.read_csv("data/risk_skills_demo.csv")
    config = {
        "data": {"id_col": "cust_id", "time_col": "loan_month", "segment_cols": ["channel"]},
        "targets": [{"name": "fpd7", "target_col": "fpd7", "observe_col": "can_7"}],
        "features": {
            "include": ["query_count_30d", "credit_score", "device_risk"] + ["x_%03d" % i for i in range(80)],
            "categorical": ["device_risk"],
        },
        "analysis": {"numeric_bins": 10, "max_features": 100},
        "output": {"enabled": True, "directory": "output/variable_analysis", "excel": True, "markdown": True},
    }
    result = VariableAnalysisSkill(config=config).run(df)
    print(result.summary.head(10).to_string(index=False))
    print(result.exports)


if __name__ == "__main__":
    main()

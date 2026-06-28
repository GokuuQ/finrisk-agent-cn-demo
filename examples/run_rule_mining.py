from __future__ import absolute_import

import pandas as pd

from risk_skills.skills import RuleMiningSkill


def main():
    df = pd.read_csv("data/risk_skills_demo.csv")
    config = {
        "data": {"time_col": "loan_month", "split_col": "split"},
        "targets": [{"name": "fpd7", "target_col": "fpd7", "observe_col": "can_7"}],
        "features": {
            "include": ["query_count_30d", "credit_score", "device_risk"] + ["x_%03d" % i for i in range(30)],
            "categorical": ["device_risk"],
        },
        "mining": {
            "min_hit_rate": 0.01,
            "max_hit_rate": 0.50,
            "min_lift": 1.20,
            "max_candidates_per_feature": 6,
            "top_single_rules_for_combine": 20,
            "enable_pairwise_and": True,
        },
        "output": {"enabled": True, "directory": "output/rule_mining", "excel": True, "markdown": True},
    }
    result = RuleMiningSkill(config=config).run(df)
    print(result.summary.head(10).to_string(index=False))
    print(result.exports)


if __name__ == "__main__":
    main()

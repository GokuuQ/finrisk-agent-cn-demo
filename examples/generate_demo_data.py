from __future__ import absolute_import

from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_PATH = Path("data/risk_skills_demo.csv")


def main():
    rng = np.random.default_rng(42)
    n = 20000
    query_count = rng.poisson(3.5, n)
    credit_score = rng.normal(620, 75, n)
    device_risk = rng.choice(["low", "mid", "high"], size=n, p=[0.58, 0.29, 0.13])
    channel = rng.choice(["app", "partner", "offline", "ad_network"], size=n, p=[0.48, 0.28, 0.12, 0.12])
    split = rng.choice(["train", "test", "oot"], size=n, p=[0.6, 0.25, 0.15])
    loan_month = rng.choice(["2026-01", "2026-02", "2026-03", "2026-04", "2026-05"], size=n)
    logit = (
        -2.5
        + 0.20 * query_count
        - 0.0065 * (credit_score - 620)
        + np.where(device_risk == "high", 0.9, 0.0)
        + np.where(channel == "ad_network", 0.35, 0.0)
        + np.where(split == "oot", 0.15, 0.0)
    )
    prob = 1.0 / (1.0 + np.exp(-logit))
    fpd7 = (rng.random(n) < prob).astype(int)
    model_score = np.clip(prob * 0.78 + rng.random(n) * 0.22, 0, 1)
    base = pd.DataFrame(
        {
            "cust_id": ["C%08d" % i for i in range(n)],
            "loan_month": loan_month,
            "channel": channel,
            "split": split,
            "query_count_30d": query_count,
            "credit_score": credit_score,
            "device_risk": device_risk,
            "fpd7": fpd7,
            "can_7": 1,
            "model_score": model_score,
        }
    )
    noise = pd.DataFrame(
        rng.normal(0, 1, size=(n, 120)),
        columns=["x_%03d" % idx for idx in range(120)],
    )
    df = pd.concat([base, noise], axis=1)
    df.loc[df.index[: int(n * 0.08)], "x_000"] = np.nan
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print("Wrote {0} rows to {1}".format(len(df), OUTPUT_PATH))


if __name__ == "__main__":
    main()

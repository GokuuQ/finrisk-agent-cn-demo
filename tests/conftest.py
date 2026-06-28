from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def wide_risk_frame() -> pd.DataFrame:
    rng = np.random.default_rng(20260628)
    n = 600
    query_count = rng.poisson(3, n)
    credit_score = rng.normal(620, 70, n)
    device_risk = rng.choice(["low", "mid", "high"], size=n, p=[0.55, 0.30, 0.15])
    channel = rng.choice(["app", "partner", "offline"], size=n, p=[0.55, 0.3, 0.15])
    split = rng.choice(["train", "test", "oot"], size=n, p=[0.6, 0.25, 0.15])
    loan_month = rng.choice(["2026-01", "2026-02", "2026-03", "2026-04"], size=n)
    logit = (
        -2.4
        + 0.22 * query_count
        - 0.007 * (credit_score - 620)
        + np.where(device_risk == "high", 1.0, 0.0)
        + np.where(channel == "partner", 0.25, 0.0)
    )
    prob = 1 / (1 + np.exp(-logit))
    fpd7 = (rng.random(n) < prob).astype(int)
    model_score = prob * 0.75 + rng.random(n) * 0.25
    df = pd.DataFrame(
        {
            "cust_id": ["C%05d" % i for i in range(n)],
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
    for idx in range(60):
        df["noise_%03d" % idx] = rng.normal(0, 1, n)
    df.loc[df.index[:40], "noise_000"] = np.nan
    return df

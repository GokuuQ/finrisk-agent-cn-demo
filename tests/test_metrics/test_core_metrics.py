from __future__ import annotations

import math

from risk_skills.metrics import calc_auc, calc_ks, calc_lift, calc_psi, calc_woe_iv, wilson_interval


def test_auc_and_ks_for_separable_scores() -> None:
    y = [0, 0, 1, 1]
    score = [0.1, 0.2, 0.8, 0.9]

    assert calc_auc(y, score)["auc"] == 1.0
    assert calc_ks(y, score)["ks"] == 1.0


def test_lift_for_hit_mask() -> None:
    result = calc_lift([1, 0, 1, 0], [True, False, True, False])

    assert result["hit_count"] == 2
    assert result["hit_bad_count"] == 2
    assert result["lift"] == 2.0


def test_woe_iv_and_psi_are_structured() -> None:
    iv = calc_woe_iv([1, 0, 1, 0], ["A", "A", "B", "B"])
    psi = calc_psi(["A", "A", "B", "B"], ["A", "B", "B", "B"])

    assert set(["detail", "total_iv", "sample_count"]).issubset(iv)
    assert iv["sample_count"] == 4
    assert psi["psi"] >= 0
    assert not psi["detail"].empty


def test_wilson_interval_bounds() -> None:
    result = wilson_interval(5, 10)

    assert 0 <= result["low"] <= result["proportion"] <= result["high"] <= 1

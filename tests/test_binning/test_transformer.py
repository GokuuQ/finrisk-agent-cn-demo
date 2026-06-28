from __future__ import annotations

from risk_skills.binning import BinTransformer


def test_bin_transformer_assigns_every_sample(wide_risk_frame) -> None:
    features = ["query_count_30d", "credit_score", "device_risk"]
    transformer = BinTransformer(
        numeric_features=["query_count_30d", "credit_score"],
        categorical_features=["device_risk"],
        n_bins=5,
    )

    binned = transformer.fit_transform(wide_risk_frame, features)

    assert list(binned.columns) == features
    assert binned.shape[0] == wide_risk_frame.shape[0]
    assert binned.isna().sum().sum() == 0

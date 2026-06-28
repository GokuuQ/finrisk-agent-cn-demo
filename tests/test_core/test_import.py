from __future__ import annotations


def test_package_imports() -> None:
    import risk_skills

    assert risk_skills.__version__ == "0.1.0"

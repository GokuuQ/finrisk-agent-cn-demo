"""Shared validation helpers for Skill inputs."""

from risk_skills.core.exceptions import InputValidationError


def require_columns(data, columns, skill_name=None, stage="validate_input"):
    """Validate that a DataFrame-like object contains required columns."""

    missing = [col for col in columns if col not in getattr(data, "columns", [])]
    if missing:
        raise InputValidationError(
            "missing required columns: {0}".format(", ".join(map(str, missing))),
            skill_name=skill_name,
            stage=stage,
        )


def require_dataframe_like(data, skill_name=None, stage="validate_input"):
    """Validate the small surface area expected from pandas DataFrame inputs."""

    if not hasattr(data, "columns") or not hasattr(data, "shape"):
        raise InputValidationError(
            "input data must be a pandas DataFrame-like object",
            skill_name=skill_name,
            stage=stage,
        )

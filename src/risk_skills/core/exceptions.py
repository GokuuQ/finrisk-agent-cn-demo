"""Project-level exceptions with explicit, locatable messages."""


class RiskSkillsError(Exception):
    """Base exception for risk-skills errors."""

    def __init__(self, message, skill_name=None, stage=None):
        self.skill_name = skill_name
        self.stage = stage
        parts = []
        if skill_name:
            parts.append("skill={0}".format(skill_name))
        if stage:
            parts.append("stage={0}".format(stage))
        if parts:
            message = "[{0}] {1}".format(" | ".join(parts), message)
        super(RiskSkillsError, self).__init__(message)


class ConfigError(RiskSkillsError):
    """Raised when configuration is invalid or cannot be loaded."""


class InputValidationError(RiskSkillsError):
    """Raised when user input does not satisfy a Skill contract."""


class DataQualityError(RiskSkillsError):
    """Raised when data quality prevents reliable computation."""


class InsufficientSampleError(RiskSkillsError):
    """Raised when sample size is insufficient for a requested metric."""


class BinningError(RiskSkillsError):
    """Raised when binning cannot be completed safely."""


class MetricCalculationError(RiskSkillsError):
    """Raised when an atomic metric cannot be calculated."""


class ExportError(RiskSkillsError):
    """Raised when report export fails."""


class OptionalDependencyError(RiskSkillsError):
    """Raised when a requested optional capability is unavailable."""

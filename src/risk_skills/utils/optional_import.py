"""Helpers for optional dependencies."""

from risk_skills.core.exceptions import OptionalDependencyError


def optional_import(module_name, feature_name=None):
    """Import an optional dependency or raise a clear project exception."""

    try:
        return __import__(module_name)
    except ImportError:
        label = feature_name or module_name
        raise OptionalDependencyError(
            "{0} requires optional dependency {1}".format(label, module_name)
        )

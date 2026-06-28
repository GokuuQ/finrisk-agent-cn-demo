"""Configuration helpers and shared specification dataclasses."""

from __future__ import absolute_import

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from risk_skills.core.exceptions import ConfigError, OptionalDependencyError


@dataclass
class TargetSpec:
    """Describe one target label and its observability contract."""

    name: str
    target_col: str
    observe_col: Optional[str] = None
    positive_value: Any = 1
    task_type: str = "risk"
    description: Optional[str] = None


@dataclass
class FeatureSpec:
    """Describe one feature and optional business metadata."""

    name: str
    feature_type: str = "auto"
    direction: int = 0
    special_values: Optional[List[Any]] = None
    manual_bins: Optional[List[Any]] = None
    description: Optional[str] = None


def load_config(config=None, path=None, defaults=None):
    """Load configuration from a dict, JSON file, or YAML file.

    Explicit dict values are merged over file values, which are merged over
    defaults. YAML support is optional and activated only when PyYAML exists.
    """

    loaded = {}
    if path:
        loaded = _load_config_file(path)
    if config is not None and not isinstance(config, dict):
        raise ConfigError("config must be a dict when provided explicitly")

    merged = {}
    if defaults:
        if not isinstance(defaults, dict):
            raise ConfigError("defaults must be a dict")
        merged = deep_merge(merged, defaults)
    merged = deep_merge(merged, loaded)
    if config:
        merged = deep_merge(merged, config)
    return merged


def _load_config_file(path):
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError("configuration file does not exist: {0}".format(config_path))

    suffix = config_path.suffix.lower()
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError("failed to read configuration file: {0}".format(exc))

    if suffix == ".json":
        try:
            return json.loads(text)
        except ValueError as exc:
            raise ConfigError("invalid JSON configuration: {0}".format(exc))

    if suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise OptionalDependencyError(
                "YAML configuration requires optional dependency PyYAML. "
                "Use JSON or install risk-skills[yaml]."
            )
        loaded = yaml.safe_load(text)
        if loaded is None:
            return {}
        if not isinstance(loaded, dict):
            raise ConfigError("YAML configuration root must be a mapping")
        return loaded

    raise ConfigError("unsupported configuration file type: {0}".format(suffix))


def deep_merge(base, override):
    """Recursively merge two dictionaries without mutating either input."""

    if not isinstance(base, dict) or not isinstance(override, dict):
        raise ConfigError("deep_merge expects dict inputs")

    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def build_target_specs(raw_targets):
    """Build TargetSpec objects from config dictionaries."""

    if raw_targets is None:
        return []
    if isinstance(raw_targets, dict):
        raw_targets = [raw_targets]
    if not isinstance(raw_targets, list):
        raise ConfigError("targets must be a list or mapping")
    targets = []
    for item in raw_targets:
        if not isinstance(item, dict):
            raise ConfigError("each target must be a mapping")
        try:
            targets.append(TargetSpec(**item))
        except TypeError as exc:
            raise ConfigError("invalid target specification: {0}".format(exc))
    return targets


def build_feature_specs(raw_features):
    """Build FeatureSpec objects from config dictionaries or feature names."""

    if raw_features is None:
        return []
    if isinstance(raw_features, dict):
        raw_features = [raw_features]
    if not isinstance(raw_features, list):
        raise ConfigError("features must be a list or mapping")
    features = []
    for item in raw_features:
        if isinstance(item, str):
            features.append(FeatureSpec(name=item))
        elif isinstance(item, dict):
            try:
                features.append(FeatureSpec(**item))
            except TypeError as exc:
                raise ConfigError("invalid feature specification: {0}".format(exc))
        else:
            raise ConfigError("each feature must be a string or mapping")
    return features

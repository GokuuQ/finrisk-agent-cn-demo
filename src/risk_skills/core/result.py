"""Standard result objects returned by all Skills."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SkillResult:
    """Structured Skill output.

    The object intentionally keeps DataFrames and other tabular objects in
    memory instead of forcing JSON serialization at the core layer.
    """

    status: str
    summary: Any = None
    details: Dict[str, Any] = field(default_factory=dict)
    charts: Dict[str, str] = field(default_factory=dict)
    exports: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def add_warning(self, message):
        self.warnings.append(str(message))


@dataclass
class RunMetadata:
    """Run-level metadata shared across Skill outputs."""

    package_version: str
    skill_name: str
    skill_version: str
    run_id: str
    run_start_time: str
    run_end_time: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    python_version: Optional[str] = None
    pandas_version: Optional[str] = None
    numpy_version: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    config_digest: Optional[str] = None
    random_state: Optional[int] = None

    def to_dict(self):
        return asdict(self)

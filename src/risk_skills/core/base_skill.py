"""Base lifecycle for all risk analysis Skills."""

from __future__ import absolute_import

import platform
import sys
import time
import uuid
from datetime import datetime

from risk_skills.core.config import load_config
from risk_skills.core.exceptions import RiskSkillsError
from risk_skills.core.result import RunMetadata, SkillResult
from risk_skills.utils.datetime import utc_now_iso
from risk_skills.utils.logging import get_logger
from risk_skills.utils.serialization import config_digest
from risk_skills.version import __version__


class BaseRiskSkill(object):
    """Unified lifecycle for offline risk analysis Skills."""

    skill_name = "base"
    skill_version = "0.1.0"

    def __init__(self, config=None, output_dir=None, logger=None):
        self.config = load_config(config=config)
        self.output_dir = output_dir or self._read_output_dir()
        self.logger = logger or get_logger(self.skill_name)
        self.warnings = []
        self.metadata = {}
        self.result = None
        self._current_stage = "init"

    def validate_input(self, data):
        raise NotImplementedError

    def prepare_data(self, data):
        return data

    def run_analysis(self, data):
        raise NotImplementedError

    def validate_result(self, result):
        return None

    def generate_summary(self, result):
        return None

    def export(self, result):
        return {}

    def run(self, data):
        """Execute the Skill lifecycle and return a SkillResult."""

        start = time.time()
        run_metadata = self._start_metadata(data)
        try:
            self._log("INFO", "validate_input", "validating input")
            self._current_stage = "validate_input"
            self.validate_input(data)

            self._log("INFO", "prepare_data", "preparing data")
            self._current_stage = "prepare_data"
            prepared = self.prepare_data(data)

            self._log("INFO", "run_analysis", "running analysis")
            self._current_stage = "run_analysis"
            result = self.run_analysis(prepared)
            if not isinstance(result, SkillResult):
                result = SkillResult(status="success", summary=result)

            self._log("INFO", "validate_result", "validating result")
            self._current_stage = "validate_result"
            self.validate_result(result)

            self._log("INFO", "generate_summary", "generating summary")
            self._current_stage = "generate_summary"
            summary = self.generate_summary(result)
            if summary is not None:
                result.summary = summary

            result.status = result.status or "success"
            result.warnings.extend([w for w in self.warnings if w not in result.warnings])
            self._finish_metadata(run_metadata, start, data)
            result.metadata.update(run_metadata.to_dict())

            if self._output_enabled():
                self._log("INFO", "export", "exporting result")
                self._current_stage = "export"
                exports = self.export(result) or {}
                result.exports.update(exports)

            self.metadata = result.metadata
            self.result = result
            self._log("INFO", "complete", "skill run completed")
            return result
        except RiskSkillsError:
            raise
        except Exception as exc:
            raise RiskSkillsError(
                "{0}: {1}".format(exc.__class__.__name__, exc),
                skill_name=self.skill_name,
                stage=self._current_stage,
            )

    def add_warning(self, message):
        warning = str(message)
        self.warnings.append(warning)
        self._log("WARNING", self._current_stage, warning)

    def _read_output_dir(self):
        output = self.config.get("output", {})
        return output.get("directory")

    def _output_enabled(self):
        output = self.config.get("output", {})
        return bool(output.get("enabled", False))

    def _start_metadata(self, data):
        row_count = None
        column_count = None
        if hasattr(data, "shape") and len(getattr(data, "shape")) >= 2:
            row_count = int(data.shape[0])
            column_count = int(data.shape[1])

        runtime = self.config.get("runtime", {})
        return RunMetadata(
            package_version=__version__,
            skill_name=self.skill_name,
            skill_version=self.skill_version,
            run_id=str(uuid.uuid4()),
            run_start_time=utc_now_iso(),
            python_version="{0}.{1}.{2}".format(
                sys.version_info.major, sys.version_info.minor, sys.version_info.micro
            ),
            pandas_version=_optional_version("pandas"),
            numpy_version=_optional_version("numpy"),
            row_count=row_count,
            column_count=column_count,
            config_digest=config_digest(self.config),
            random_state=runtime.get("random_state"),
        )

    def _finish_metadata(self, metadata, start, data):
        metadata.run_end_time = utc_now_iso()
        metadata.elapsed_seconds = round(time.time() - start, 6)

    def _log(self, level, stage, message):
        extra = {"skill": self.skill_name, "stage": stage}
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message, extra=extra)


def _optional_version(package_name):
    try:
        module = __import__(package_name)
    except ImportError:
        return None
    return getattr(module, "__version__", None)

"""Logging utilities with consistent Skill context fields."""

import logging
import sys


class SkillLogFormatter(logging.Formatter):
    """Formatter that tolerates records without Skill metadata."""

    def format(self, record):
        if not hasattr(record, "skill"):
            record.skill = "-"
        if not hasattr(record, "stage"):
            record.stage = "-"
        return super(SkillLogFormatter, self).format(record)


def get_logger(name="risk_skills", level=logging.INFO):
    """Create or reuse a console logger for Skill execution."""

    logger_name = "risk_skills.{0}".format(name)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            SkillLogFormatter(
                "%(asctime)s | %(levelname)s | %(skill)s | %(stage)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
    return logger

"""Minimal in-memory Skill registry for future orchestration."""

from risk_skills.core.exceptions import ConfigError


class SkillRegistry(object):
    """Register and resolve Skill classes by name."""

    def __init__(self):
        self._skills = {}

    def register(self, skill_cls):
        name = getattr(skill_cls, "skill_name", None)
        if not name:
            raise ConfigError("skill class must define skill_name")
        self._skills[name] = skill_cls
        return skill_cls

    def get(self, name):
        try:
            return self._skills[name]
        except KeyError:
            raise ConfigError("unknown skill: {0}".format(name))

    def names(self):
        return sorted(self._skills)


registry = SkillRegistry()

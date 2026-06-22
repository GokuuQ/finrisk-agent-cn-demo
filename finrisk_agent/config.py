from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class LLMConfig:
    enabled: bool = False
    provider: str = "local_openai_compatible"
    base_url: str = "http://localhost:11434/v1"
    model: str = "qwen2.5-coder:7b"
    temperature: float = 0.1
    timeout_seconds: int = 60


@dataclass(frozen=True)
class DatabaseConfig:
    path: str = "data/finrisk_demo.sqlite"


@dataclass(frozen=True)
class AgentConfig:
    max_rows: int = 200
    demo_mode_notice: bool = True


@dataclass(frozen=True)
class AppConfig:
    llm: LLMConfig
    database: DatabaseConfig
    agent: AgentConfig


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        config_path = Path("config.example.yaml")

    raw: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file) or {}

    return AppConfig(
        llm=LLMConfig(**raw.get("llm", {})),
        database=DatabaseConfig(**raw.get("database", {})),
        agent=AgentConfig(**raw.get("agent", {})),
    )

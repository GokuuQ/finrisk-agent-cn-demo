from __future__ import annotations

from dataclasses import dataclass

import requests

from finrisk_agent.config import LLMConfig


@dataclass
class LocalLLMClient:
    config: LLMConfig

    def chat(self, system_prompt: str, user_prompt: str) -> str | None:
        if not self.config.enabled:
            return None

        if self.config.provider != "local_openai_compatible":
            raise ValueError(f"Unsupported provider: {self.config.provider}")

        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        response = requests.post(url, json=payload, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

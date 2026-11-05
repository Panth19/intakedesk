from __future__ import annotations

import os
from typing import Any


PROVIDERS = {
    "groq": {
        "label": "Groq (free tier, recommended)",
        "default_base_url": "https://api.groq.com/openai/v1",
        "default_model": "openai/gpt-oss-20b",
        "signup": "https://console.groq.com/keys",
        "input_eur_per_m": 0.04,
        "output_eur_per_m": 0.04,
    },
    "openai": {
        "label": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "signup": "https://platform.openai.com/api-keys",
        "input_eur_per_m": 0.14,
        "output_eur_per_m": 0.55,
    },
    "openrouter": {
        "label": "OpenRouter",
        "default_base_url": "https://openrouter.ai/api/v1",
        "default_model": "openai/gpt-4o-mini",
        "signup": "https://openrouter.ai/keys",
        "input_eur_per_m": 0.14,
        "output_eur_per_m": 0.55,
    },
    "custom": {
        "label": "Custom OpenAI-compatible",
        "default_base_url": "https://api.example.com/v1",
        "default_model": "your-model",
        "signup": "",
        "input_eur_per_m": 0.10,
        "output_eur_per_m": 0.10,
    },
}


class LlmSettings:
    def __init__(self) -> None:
        self.enabled = os.getenv("USER_LLM_ENABLED", "").lower() in {"1", "true", "yes"}
        self.provider = os.getenv("USER_LLM_PROVIDER", "groq").strip() or "groq"
        self.api_key = os.getenv("USER_LLM_API_KEY", "").strip()
        self.base_url = os.getenv("USER_LLM_BASE_URL", "").strip()
        self.model = os.getenv("USER_LLM_MODEL", "").strip()
        self.apply_defaults()

    def apply_defaults(self) -> None:
        spec = PROVIDERS.get(self.provider, PROVIDERS["custom"])
        if not self.base_url:
            self.base_url = spec["default_base_url"]
        if not self.model:
            self.model = spec["default_model"]
        self.enabled = bool(self.enabled and self.api_key)

    def update(self, payload: dict[str, Any]) -> None:
        if "provider" in payload and payload["provider"]:
            self.provider = str(payload["provider"]).strip()
        if "api_key" in payload:
            key = str(payload.get("api_key") or "").strip()
            if key and not key.endswith("••••"):
                self.api_key = key
        if "base_url" in payload and payload["base_url"] is not None:
            self.base_url = str(payload["base_url"]).strip()
        if "model" in payload and payload["model"] is not None:
            self.model = str(payload["model"]).strip()
        if "enabled" in payload:
            self.enabled = bool(payload["enabled"])
        self.apply_defaults()
        self.enabled = bool(self.enabled and self.api_key)

    def public(self) -> dict[str, Any]:
        spec = PROVIDERS.get(self.provider, PROVIDERS["custom"])
        masked = ""
        if self.api_key:
            masked = self.api_key[:4] + "••••" + self.api_key[-4:]
        return {
            "enabled": self.enabled,
            "configured": bool(self.api_key),
            "provider": self.provider,
            "provider_label": spec["label"],
            "base_url": self.base_url,
            "model": self.model,
            "api_key_masked": masked,
            "signup": spec.get("signup", ""),
            "mode": "llm" if self.enabled else "rules",
            "providers": [
                {
                    "id": pid,
                    "label": p["label"],
                    "default_base_url": p["default_base_url"],
                    "default_model": p["default_model"],
                    "signup": p["signup"],
                }
                for pid, p in PROVIDERS.items()
            ],
        }


llm_settings = LlmSettings()

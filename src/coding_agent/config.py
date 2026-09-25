from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping


DEFAULT_MODEL = "gpt-6-sol"
DEFAULT_MAX_STEPS = 20


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


@dataclass(frozen=True)
class AgentConfig:
    """Model/runtime configuration resolved before the agent starts."""

    api_key: str | None = field(default=None, repr=False)
    base_url: str | None = None
    model: str = DEFAULT_MODEL
    max_steps: int = DEFAULT_MAX_STEPS

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model must not be empty.")
        if self.max_steps <= 0:
            raise ValueError("max_steps must be greater than zero.")

    @classmethod
    def from_sources(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_steps: int | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> "AgentConfig":
        """Resolve config with precedence: explicit argument > environment > default."""
        env = os.environ if environ is None else environ

        resolved_api_key = _clean_optional(api_key) or _clean_optional(
            env.get("OPENAI_API_KEY")
        )
        resolved_base_url = _clean_optional(base_url) or _clean_optional(
            env.get("OPENAI_BASE_URL")
        )
        resolved_model = (
            _clean_optional(model)
            or _clean_optional(env.get("OPENAI_MODEL"))
            or DEFAULT_MODEL
        )

        if max_steps is not None:
            resolved_max_steps = max_steps
        else:
            raw_max_steps = _clean_optional(env.get("CODING_AGENT_MAX_STEPS"))
            if raw_max_steps is None:
                resolved_max_steps = DEFAULT_MAX_STEPS
            else:
                try:
                    resolved_max_steps = int(raw_max_steps)
                except ValueError as exc:
                    raise ValueError(
                        "CODING_AGENT_MAX_STEPS must be an integer."
                    ) from exc

        return cls(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            model=resolved_model,
            max_steps=resolved_max_steps,
        )

    def openai_client_kwargs(self) -> dict[str, str]:
        """Return only the connection options that should be passed to OpenAI()."""
        kwargs: dict[str, str] = {}
        if self.api_key is not None:
            kwargs["api_key"] = self.api_key
        if self.base_url is not None:
            kwargs["base_url"] = self.base_url
        return kwargs

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping


DEFAULT_MODEL = "gpt-6-sol"
DEFAULT_MAX_STEPS = 20
DEFAULT_CONTEXT_MAX_CHARS = 40_000
DEFAULT_CONTEXT_RECENT_ITEMS = 8


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _read_int_env(
    env: Mapping[str, str],
    name: str,
    default: int,
) -> int:
    raw = _clean_optional(env.get(name))
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc


@dataclass(frozen=True)
class AgentConfig:
    """Model/runtime configuration resolved before the agent starts."""

    api_key: str | None = field(default=None, repr=False)
    base_url: str | None = None
    model: str = DEFAULT_MODEL
    max_steps: int = DEFAULT_MAX_STEPS
    context_max_chars: int = DEFAULT_CONTEXT_MAX_CHARS
    context_recent_items: int = DEFAULT_CONTEXT_RECENT_ITEMS

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model must not be empty.")
        if self.max_steps <= 0:
            raise ValueError("max_steps must be greater than zero.")
        if self.context_max_chars <= 0:
            raise ValueError("context_max_chars must be greater than zero.")
        if self.context_recent_items < 0:
            raise ValueError("context_recent_items must not be negative.")

    @classmethod
    def from_sources(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_steps: int | None = None,
        context_max_chars: int | None = None,
        context_recent_items: int | None = None,
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

        resolved_max_steps = (
            max_steps
            if max_steps is not None
            else _read_int_env(
                env,
                "CODING_AGENT_MAX_STEPS",
                DEFAULT_MAX_STEPS,
            )
        )
        resolved_context_max_chars = (
            context_max_chars
            if context_max_chars is not None
            else _read_int_env(
                env,
                "CODING_AGENT_CONTEXT_MAX_CHARS",
                DEFAULT_CONTEXT_MAX_CHARS,
            )
        )
        resolved_context_recent_items = (
            context_recent_items
            if context_recent_items is not None
            else _read_int_env(
                env,
                "CODING_AGENT_CONTEXT_RECENT_ITEMS",
                DEFAULT_CONTEXT_RECENT_ITEMS,
            )
        )

        return cls(
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            model=resolved_model,
            max_steps=resolved_max_steps,
            context_max_chars=resolved_context_max_chars,
            context_recent_items=resolved_context_recent_items,
        )

    def openai_client_kwargs(self) -> dict[str, str]:
        """Return only the connection options that should be passed to OpenAI()."""
        kwargs: dict[str, str] = {}
        if self.api_key is not None:
            kwargs["api_key"] = self.api_key
        if self.base_url is not None:
            kwargs["base_url"] = self.base_url
        return kwargs

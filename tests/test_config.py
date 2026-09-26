import pytest

from coding_agent.config import (
    DEFAULT_CONTEXT_MAX_CHARS,
    DEFAULT_CONTEXT_RECENT_ITEMS,
    DEFAULT_MAX_STEPS,
    DEFAULT_MODEL,
    AgentConfig,
)


def test_config_uses_defaults_without_overrides() -> None:
    config = AgentConfig.from_sources(environ={})

    assert config.api_key is None
    assert config.base_url is None
    assert config.model == DEFAULT_MODEL
    assert config.max_steps == DEFAULT_MAX_STEPS
    assert config.context_max_chars == DEFAULT_CONTEXT_MAX_CHARS
    assert config.context_recent_items == DEFAULT_CONTEXT_RECENT_ITEMS


def test_explicit_values_override_environment() -> None:
    config = AgentConfig.from_sources(
        api_key="cli-key",
        base_url="https://cli.example/v1",
        model="cli-model",
        max_steps=7,
        context_max_chars=1234,
        context_recent_items=3,
        environ={
            "OPENAI_API_KEY": "env-key",
            "OPENAI_BASE_URL": "https://env.example/v1",
            "OPENAI_MODEL": "env-model",
            "CODING_AGENT_MAX_STEPS": "99",
            "CODING_AGENT_CONTEXT_MAX_CHARS": "9999",
            "CODING_AGENT_CONTEXT_RECENT_ITEMS": "9",
        },
    )

    assert config.api_key == "cli-key"
    assert config.base_url == "https://cli.example/v1"
    assert config.model == "cli-model"
    assert config.max_steps == 7
    assert config.context_max_chars == 1234
    assert config.context_recent_items == 3


def test_config_reads_environment() -> None:
    config = AgentConfig.from_sources(
        environ={
            "OPENAI_API_KEY": "env-key",
            "OPENAI_BASE_URL": "https://example.com/v1",
            "OPENAI_MODEL": "custom-model",
            "CODING_AGENT_MAX_STEPS": "12",
            "CODING_AGENT_CONTEXT_MAX_CHARS": "20000",
            "CODING_AGENT_CONTEXT_RECENT_ITEMS": "4",
        }
    )

    assert config.api_key == "env-key"
    assert config.base_url == "https://example.com/v1"
    assert config.model == "custom-model"
    assert config.max_steps == 12
    assert config.context_max_chars == 20000
    assert config.context_recent_items == 4


def test_api_key_is_hidden_from_repr() -> None:
    config = AgentConfig(api_key="super-secret")

    assert "super-secret" not in repr(config)


def test_invalid_environment_max_steps_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        AgentConfig.from_sources(
            environ={"CODING_AGENT_MAX_STEPS": "not-a-number"}
        )


def test_invalid_environment_context_budget_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        AgentConfig.from_sources(
            environ={"CODING_AGENT_CONTEXT_MAX_CHARS": "not-a-number"}
        )


def test_non_positive_max_steps_is_rejected() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        AgentConfig.from_sources(max_steps=0, environ={})


def test_invalid_context_settings_are_rejected() -> None:
    with pytest.raises(ValueError, match="context_max_chars"):
        AgentConfig(context_max_chars=0)

    with pytest.raises(ValueError, match="context_recent_items"):
        AgentConfig(context_recent_items=-1)


def test_openai_client_kwargs_only_include_configured_connection_values() -> None:
    empty = AgentConfig()
    configured = AgentConfig(
        api_key="key",
        base_url="https://example.com/v1",
    )

    assert empty.openai_client_kwargs() == {}
    assert configured.openai_client_kwargs() == {
        "api_key": "key",
        "base_url": "https://example.com/v1",
    }

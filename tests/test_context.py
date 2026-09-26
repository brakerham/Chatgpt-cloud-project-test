from types import SimpleNamespace

import pytest

from coding_agent.context import AgentState, ContextManager


class FakeCompressor:
    def __init__(self, result: str = "compressed summary") -> None:
        self.result = result
        self.calls: list[dict] = []

    def compress(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return self.result


def test_agent_state_rejects_empty_task() -> None:
    with pytest.raises(ValueError, match="Task must not be empty"):
        AgentState(task="   ")


def test_context_manager_creates_initial_user_context() -> None:
    manager = ContextManager()

    state = manager.create_state("Inspect the project")

    assert state.task == "Inspect the project"
    assert state.step == 0
    assert state.history == [
        {"role": "user", "content": "Inspect the project"}
    ]


def test_build_input_returns_a_copy() -> None:
    manager = ContextManager()
    state = manager.create_state("Task")

    model_input = manager.build_input(state)
    model_input.append({"role": "user", "content": "mutated copy"})

    assert len(state.history) == 1


def test_context_manager_records_model_and_tool_output() -> None:
    manager = ContextManager()
    state = manager.create_state("Task")
    model_item = SimpleNamespace(type="function_call", call_id="call_1")

    manager.record_model_output(state, [model_item])
    manager.record_tool_result(
        state,
        call_id="call_1",
        result={"ok": True, "path": "hello.py"},
    )

    assert state.history[1] is model_item
    assert state.history[2]["type"] == "function_call_output"
    assert state.history[2]["call_id"] == "call_1"
    assert '"ok": true' in state.history[2]["output"]


def test_context_manager_tracks_steps() -> None:
    manager = ContextManager()
    state = manager.create_state("Task")

    manager.advance_step(state)
    manager.advance_step(state)

    assert state.step == 2


def test_context_does_not_compress_below_threshold() -> None:
    manager = ContextManager(max_context_chars=10_000, recent_items=2)
    state = manager.create_state("Task")
    state.history.append({"role": "assistant", "content": "small"})
    compressor = FakeCompressor()

    compressed = manager.maybe_compress(state, compressor)

    assert compressed is False
    assert compressor.calls == []
    assert state.compression_count == 0


def test_context_compresses_old_history_and_preserves_recent_event() -> None:
    manager = ContextManager(max_context_chars=180, recent_items=1)
    state = manager.create_state("Task")
    state.history.extend(
        [
            {"role": "assistant", "content": "older-" + ("x" * 220)},
            {"role": "assistant", "content": "recent-event"},
        ]
    )
    compressor = FakeCompressor("summary-v1")

    compressed = manager.maybe_compress(state, compressor)

    assert compressed is True
    assert state.summary == "summary-v1"
    assert state.recent_context is not None
    assert "recent-event" in state.recent_context
    assert state.history == [{"role": "user", "content": "Task"}]
    assert state.compression_count == 1
    assert len(compressor.calls) == 1
    assert "older-" in compressor.calls[0]["history_text"]

    model_input = manager.build_input(state)
    assert model_input[0] == {"role": "user", "content": "Task"}
    assert "summary-v1" in model_input[1]["content"]
    assert "recent-event" in model_input[2]["content"]


def test_recompression_folds_previous_recent_context_into_summary() -> None:
    manager = ContextManager(max_context_chars=120, recent_items=0)
    state = manager.create_state("Task")
    state.summary = "summary-v1"
    state.recent_context = "previous recent event"
    state.history.append(
        {"role": "assistant", "content": "new-" + ("y" * 180)}
    )
    compressor = FakeCompressor("summary-v2")

    compressed = manager.maybe_compress(state, compressor)

    assert compressed is True
    assert state.summary == "summary-v2"
    assert state.recent_context is None
    assert state.compression_count == 1
    assert compressor.calls[0]["previous_summary"] == "summary-v1"
    assert "previous recent event" in compressor.calls[0]["history_text"]
    assert "new-" in compressor.calls[0]["history_text"]

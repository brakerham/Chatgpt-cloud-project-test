from types import SimpleNamespace

import pytest

from coding_agent.context import AgentState, ContextManager


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

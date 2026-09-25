from __future__ import annotations

import json
from typing import Any

from .state import AgentState


class ContextManager:
    """Owns how one agent run stores and rebuilds model context."""

    def create_state(self, task: str) -> AgentState:
        state = AgentState(task=task)
        state.history.append({"role": "user", "content": task})
        return state

    def build_input(self, state: AgentState) -> list[Any]:
        """Return the current model input without exposing the mutable history list."""
        return list(state.history)

    def record_model_output(self, state: AgentState, output: list[Any]) -> None:
        """Preserve model output so stateless Responses calls can replay it."""
        state.history.extend(output)

    def record_tool_result(
        self,
        state: AgentState,
        *,
        call_id: str,
        result: dict[str, Any],
    ) -> None:
        state.history.append(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result, ensure_ascii=False),
            }
        )

    def advance_step(self, state: AgentState) -> None:
        state.step += 1

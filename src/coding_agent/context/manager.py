from __future__ import annotations

import json
from typing import Any

from .compressor import ContextCompressor
from .state import AgentState


class ContextManager:
    """Owns how one agent run stores, compresses, and rebuilds model context."""

    def __init__(
        self,
        *,
        max_context_chars: int = 40_000,
        recent_items: int = 8,
    ) -> None:
        if max_context_chars <= 0:
            raise ValueError("max_context_chars must be greater than zero.")
        if recent_items < 0:
            raise ValueError("recent_items must not be negative.")

        self.max_context_chars = max_context_chars
        self.recent_items = recent_items

    def create_state(self, task: str) -> AgentState:
        state = AgentState(task=task)
        state.history.append({"role": "user", "content": task})
        return state

    def build_input(self, state: AgentState) -> list[Any]:
        """Build model input from compressed context plus new raw history."""
        if not state.history:
            raise RuntimeError("AgentState history must contain the original task.")

        items: list[Any] = [state.history[0]]

        if state.summary:
            items.append(
                {
                    "role": "assistant",
                    "content": (
                        "[Compressed earlier execution context]\n"
                        f"{state.summary}"
                    ),
                }
            )

        if state.recent_context:
            items.append(
                {
                    "role": "assistant",
                    "content": (
                        "[Recent execution events preserved from before compression]\n"
                        f"{state.recent_context}"
                    ),
                }
            )

        items.extend(state.history[1:])
        return items

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

    def estimate_context_chars(self, state: AgentState) -> int:
        return sum(len(self._serialize(item)) for item in self.build_input(state))

    def should_compress(self, state: AgentState) -> bool:
        if len(state.history) <= 1 and not state.summary and not state.recent_context:
            return False
        return self.estimate_context_chars(state) > self.max_context_chars

    def maybe_compress(
        self,
        state: AgentState,
        compressor: ContextCompressor,
    ) -> bool:
        if not self.should_compress(state):
            return False

        raw_items = state.history[1:]
        serialized = [self._serialize(item) for item in raw_items]

        recent_budget = self.max_context_chars // 2
        recent_parts: list[str] = []
        recent_size = 0

        for text in reversed(serialized):
            if len(recent_parts) >= self.recent_items:
                break
            if recent_parts and recent_size + len(text) > recent_budget:
                break
            if not recent_parts and len(text) > recent_budget:
                break

            recent_parts.append(text)
            recent_size += len(text)

        recent_parts.reverse()
        recent_count = len(recent_parts)
        older_parts = serialized[: len(serialized) - recent_count]

        # A compression pass must actually remove at least one raw history item.
        if not older_parts and recent_parts:
            older_parts.append(recent_parts.pop(0))

        history_to_summarize: list[str] = []
        if state.recent_context:
            history_to_summarize.append(
                "Previously preserved recent events:\n" + state.recent_context
            )
        history_to_summarize.extend(older_parts)

        if not history_to_summarize and not state.summary:
            return False

        new_summary = compressor.compress(
            task=state.task,
            previous_summary=state.summary,
            history_text=(
                "\n\n".join(history_to_summarize)
                if history_to_summarize
                else "(No additional older events.)"
            ),
        )

        state.summary = new_summary
        state.recent_context = "\n\n".join(recent_parts) or None
        state.history = [state.history[0]]
        state.compression_count += 1
        state.metadata["last_compression_step"] = state.step
        return True

    def _serialize(self, value: Any) -> str:
        return json.dumps(
            self._jsonable(value),
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )

    def _jsonable(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {str(key): self._jsonable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._jsonable(item) for item in value]
        if hasattr(value, "model_dump"):
            return self._jsonable(value.model_dump(mode="json"))
        if hasattr(value, "__dict__"):
            return {
                key: self._jsonable(item)
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        return str(value)

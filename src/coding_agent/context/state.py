from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """Mutable runtime state for one CodingAgent run."""

    task: str
    history: list[Any] = field(default_factory=list)
    step: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError("Task must not be empty.")
        if self.step < 0:
            raise ValueError("step must not be negative.")

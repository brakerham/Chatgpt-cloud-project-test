from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """Mutable runtime state for one CodingAgent run."""

    task: str
    history: list[Any] = field(default_factory=list)
    summary: str | None = None
    recent_context: str | None = None
    step: int = 0
    compression_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError("Task must not be empty.")
        if self.step < 0:
            raise ValueError("step must not be negative.")
        if self.compression_count < 0:
            raise ValueError("compression_count must not be negative.")

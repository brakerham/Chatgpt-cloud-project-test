from __future__ import annotations

from typing import Any


COMPRESSION_INSTRUCTIONS = """You compress execution history for a coding agent.

Produce a concise, factual summary that lets the agent continue the same task
without replaying the full history.

Use these sections:
- Goal
- Completed work
- Files and artifacts
- Tests and checks
- Important decisions and constraints
- Errors and unresolved issues
- Next likely action

Rules:
- Preserve concrete file paths, commands, error messages, and decisions when relevant.
- Preserve unresolved failures and safety constraints.
- Do not invent work, test results, or decisions.
- Prefer compact facts over narrative prose.
"""


class ContextCompressor:
    """Uses the configured model to summarize older completed agent history."""

    def __init__(self, client: Any, model: str) -> None:
        self.client = client
        self.model = model

    def compress(
        self,
        *,
        task: str,
        previous_summary: str | None,
        history_text: str,
    ) -> str:
        previous = previous_summary or "(none)"

        response = self.client.responses.create(
            model=self.model,
            instructions=COMPRESSION_INSTRUCTIONS,
            input=[
                {
                    "role": "user",
                    "content": (
                        "Original task:\n"
                        f"{task}\n\n"
                        "Previous compressed summary:\n"
                        f"{previous}\n\n"
                        "Older execution history to merge into the summary:\n"
                        f"{history_text}"
                    ),
                }
            ],
            store=False,
        )

        summary = (response.output_text or "").strip()
        if not summary:
            raise RuntimeError("Context compressor returned an empty summary.")
        return summary

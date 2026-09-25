from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from .tools import CodingTools
from .workspace import Workspace


DEFAULT_MODEL = "gpt-6-sol"

SYSTEM_PROMPT = """You are a minimal Coding Agent working inside one workspace.

Rules:
1. Inspect relevant existing files before modifying them.
2. Never guess file contents; use the file tools.
3. Make the smallest coherent change that solves the user's task.
4. All file access must go through the provided tools.
5. After modifying code, run relevant tests or checks when possible.
6. Never claim a test passed unless you actually ran it successfully.
7. Never access files outside the workspace.
8. Never modify Git history or create commits.
9. If a tool fails, use the error message to decide what to do next.
10. When finished, briefly summarize what changed and what was tested.
"""


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "list_files",
        "description": "List files inside the workspace. Use '.' for the workspace root.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative workspace path."}
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Read one UTF-8 text file from the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative file path."}
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "write_file",
        "description": "Create or fully replace one UTF-8 text file in the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative file path."},
                "content": {"type": "string", "description": "Complete new file content."},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "run_command",
        "description": (
            "Run one allow-listed development program in the workspace. "
            "Git is restricted to read-only subcommands."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "program": {"type": "string"},
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Arguments passed directly to the program without a shell.",
                },
            },
            "required": ["program", "args"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


class CodingAgent:
    """A small, explicit LLM -> tool -> result agent loop."""

    def __init__(
        self,
        workspace: str | Path,
        model: str = DEFAULT_MODEL,
        max_steps: int = 20,
        client: Any | None = None,
    ) -> None:
        if max_steps <= 0:
            raise ValueError("max_steps must be greater than zero.")

        self.model = model
        self.max_steps = max_steps
        self.tools = CodingTools(Workspace(workspace))
        self.client = client if client is not None else OpenAI()

    def _execute_tool_call(self, call: Any) -> dict[str, Any]:
        try:
            arguments = json.loads(call.arguments)
            if not isinstance(arguments, dict):
                raise ValueError("Tool arguments must decode to a JSON object.")
            return self.tools.call(call.name, arguments)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            return {"ok": False, "error": f"Invalid tool call: {exc}"}
        except Exception as exc:  # Keep a tool failure inside the agent loop.
            return {"ok": False, "error": f"Tool execution failed: {exc}"}

    def run(self, task: str) -> str:
        if not task.strip():
            raise ValueError("Task must not be empty.")

        input_items: list[Any] = [{"role": "user", "content": task}]

        for _ in range(self.max_steps):
            response = self.client.responses.create(
                model=self.model,
                instructions=SYSTEM_PROMPT,
                input=input_items,
                tools=TOOL_DEFINITIONS,
                parallel_tool_calls=False,
                store=False,
            )

            # Preserve all model output, including reasoning items and tool calls.
            input_items.extend(response.output)

            tool_calls = [
                item
                for item in response.output
                if getattr(item, "type", None) == "function_call"
            ]

            if not tool_calls:
                final_text = (response.output_text or "").strip()
                if not final_text:
                    raise RuntimeError("The model stopped without a final text response.")
                return final_text

            for call in tool_calls:
                result = self._execute_tool_call(call)
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(result, ensure_ascii=False),
                    }
                )

        raise RuntimeError(
            f"Agent exceeded the maximum of {self.max_steps} model steps."
        )

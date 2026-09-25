from __future__ import annotations

import shutil
import subprocess
from typing import Any

from .workspace import Workspace


ALLOWED_PROGRAMS = frozenset(
    {"python", "pytest", "ruff", "mypy", "git", "node", "npm", "pnpm", "go", "cargo"}
)
READ_ONLY_GIT_COMMANDS = frozenset({"status", "diff", "log", "show"})


class CodingTools:
    """The four tools exposed to the language model."""

    def __init__(
        self,
        workspace: Workspace,
        command_timeout: int = 30,
        max_output_chars: int = 8_000,
    ) -> None:
        self.workspace = workspace
        self.command_timeout = command_timeout
        self.max_output_chars = max_output_chars

    @staticmethod
    def _error(exc: Exception | str) -> dict[str, Any]:
        return {"ok": False, "error": str(exc)}

    def list_files(self, path: str) -> dict[str, Any]:
        try:
            files = self.workspace.list_files(path)
            return {"ok": True, "files": files, "count": len(files)}
        except (OSError, ValueError) as exc:
            return self._error(exc)

    def read_file(self, path: str) -> dict[str, Any]:
        try:
            content = self.workspace.read_text(path)
            return {"ok": True, "path": path, "content": content}
        except (OSError, UnicodeError, ValueError) as exc:
            return self._error(exc)

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        try:
            self.workspace.write_text(path, content)
            return {
                "ok": True,
                "path": path,
                "characters_written": len(content),
            }
        except (OSError, UnicodeError, ValueError) as exc:
            return self._error(exc)

    def run_command(self, program: str, args: list[str]) -> dict[str, Any]:
        normalized_program = program.strip().lower()

        if normalized_program not in ALLOWED_PROGRAMS:
            return self._error(f"Program is not allowed: {program}")

        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            return self._error("Command args must be a list of strings.")

        if normalized_program == "git":
            if not args or args[0] not in READ_ONLY_GIT_COMMANDS:
                return self._error(
                    "Only read-only git commands are allowed: status, diff, log, show."
                )

        executable = shutil.which(normalized_program)
        if executable is None:
            return self._error(f"Program was not found on PATH: {normalized_program}")

        try:
            completed = subprocess.run(
                [executable, *args],
                cwd=self.workspace.root,
                capture_output=True,
                text=True,
                timeout=self.command_timeout,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return self._error(
                f"Command timed out after {self.command_timeout} seconds."
            )
        except OSError as exc:
            return self._error(exc)

        stdout = completed.stdout[-self.max_output_chars :]
        stderr = completed.stderr[-self.max_output_chars :]

        return {
            "ok": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "list_files":
            return self.list_files(**arguments)
        if name == "read_file":
            return self.read_file(**arguments)
        if name == "write_file":
            return self.write_file(**arguments)
        if name == "run_command":
            return self.run_command(**arguments)
        return self._error(f"Unknown tool: {name}")

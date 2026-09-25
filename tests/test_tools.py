from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from coding_agent.tools import CodingTools
from coding_agent.workspace import Workspace


def make_tools(tmp_path: Path) -> CodingTools:
    return CodingTools(Workspace(tmp_path))


def test_write_then_read_file_and_create_parent_directories(tmp_path: Path) -> None:
    tools = make_tools(tmp_path)

    written = tools.write_file("src/example.py", "print('hello')\n")
    read = tools.read_file("src/example.py")

    assert written["ok"] is True
    assert (tmp_path / "src" / "example.py").exists()
    assert read == {
        "ok": True,
        "path": "src/example.py",
        "content": "print('hello')\n",
    }


def test_read_file_reports_missing_file(tmp_path: Path) -> None:
    tools = make_tools(tmp_path)

    result = tools.read_file("missing.py")

    assert result["ok"] is False
    assert "does not exist" in result["error"]


def test_list_files_ignores_special_directories(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("pass\n", encoding="utf-8")

    for ignored in [".git", ".venv", "__pycache__", "node_modules"]:
        directory = tmp_path / ignored
        directory.mkdir()
        (directory / "ignored.txt").write_text("ignore me", encoding="utf-8")

    tools = make_tools(tmp_path)
    result = tools.list_files(".")

    assert result["ok"] is True
    assert result["files"] == ["src/app.py"]


def test_run_command_executes_allowed_program(
    tmp_path: Path, monkeypatch
) -> None:
    tools = make_tools(tmp_path)
    original_which = shutil.which

    def fake_which(program: str) -> str | None:
        if program == "python":
            return sys.executable
        return original_which(program)

    monkeypatch.setattr(shutil, "which", fake_which)

    result = tools.run_command("python", ["-c", "print('agent-ok')"])

    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert result["stdout"].strip() == "agent-ok"


def test_run_command_rejects_non_allowlisted_program(tmp_path: Path) -> None:
    tools = make_tools(tmp_path)

    result = tools.run_command("bash", ["-c", "echo no"])

    assert result["ok"] is False
    assert "not allowed" in result["error"]


def test_run_command_rejects_git_write_command(tmp_path: Path) -> None:
    tools = make_tools(tmp_path)

    result = tools.run_command("git", ["commit", "-m", "no"])

    assert result["ok"] is False
    assert "read-only git commands" in result["error"]


def test_run_command_reports_timeout(tmp_path: Path, monkeypatch) -> None:
    tools = CodingTools(Workspace(tmp_path), command_timeout=1)

    monkeypatch.setattr(shutil, "which", lambda program: sys.executable)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = tools.run_command("python", ["-c", "print('never')"])

    assert result["ok"] is False
    assert result["error"] == "Command timed out after 1 seconds."

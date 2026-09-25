from pathlib import Path

import pytest

from coding_agent.workspace import Workspace


def test_workspace_resolves_internal_path(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path)

    resolved = workspace.resolve("src/app.py")

    assert resolved == (tmp_path / "src" / "app.py").resolve()


def test_workspace_blocks_parent_escape(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path)

    with pytest.raises(ValueError, match="escapes the workspace"):
        workspace.resolve("../outside.txt")


def test_workspace_blocks_absolute_paths(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path)

    with pytest.raises(ValueError, match="Absolute paths"):
        workspace.resolve(tmp_path / "absolute.txt")

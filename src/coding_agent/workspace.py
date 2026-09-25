from __future__ import annotations

import os
from pathlib import Path


IGNORED_DIRS = frozenset({".git", ".venv", "__pycache__", "node_modules"})


class Workspace:
    """Confines file access to one project directory."""

    def __init__(self, root: str | Path) -> None:
        resolved_root = Path(root).expanduser().resolve()
        if not resolved_root.exists():
            raise ValueError(f"Workspace does not exist: {resolved_root}")
        if not resolved_root.is_dir():
            raise ValueError(f"Workspace is not a directory: {resolved_root}")
        self.root = resolved_root

    def resolve(self, path: str | Path) -> Path:
        """Resolve a relative path and reject paths that escape the workspace."""
        relative_path = Path(path)
        if relative_path.is_absolute():
            raise ValueError("Absolute paths are not allowed.")

        target = (self.root / relative_path).resolve(strict=False)
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Path escapes the workspace: {path}") from exc
        return target

    def relative_name(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def list_files(self, path: str | Path = ".", limit: int = 200) -> list[str]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        base = self.resolve(path)
        if not base.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        if base.is_file():
            return [self.relative_name(base)]

        relative_base = base.relative_to(self.root)
        if any(part in IGNORED_DIRS for part in relative_base.parts):
            return []

        files: list[str] = []
        for current_root, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(
                dirname for dirname in dirnames if dirname not in IGNORED_DIRS
            )

            for filename in sorted(filenames):
                file_path = Path(current_root) / filename
                files.append(self.relative_name(file_path))
                if len(files) >= limit:
                    return files

        return files

    def read_text(self, path: str | Path) -> str:
        file_path = self.resolve(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        return file_path.read_text(encoding="utf-8")

    def write_text(self, path: str | Path, content: str) -> None:
        file_path = self.resolve(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

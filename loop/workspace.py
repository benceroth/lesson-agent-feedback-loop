"""Workspace helpers: fresh copy of the starter, deterministic file IO."""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path

from loop.task import Task

PYTEST_INI = "[pytest]\npythonpath = src\n"
_IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc")


def write_text_lf(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.replace("\r\n", "\n").encode("utf-8"))


def create_workspace(task: Task, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(task.starter_dir, dest, ignore=_IGNORE)
    write_text_lf(dest / "pytest.ini", PYTEST_INI)
    return dest


def read_files(root: Path) -> dict[str, str]:
    """Files the builder may read: sources and tests, never config or hidden checks."""
    files: dict[str, str] = {}
    for file in sorted(root.rglob("*.py")):
        if "__pycache__" in file.parts:
            continue
        files[file.relative_to(root).as_posix()] = file.read_text(encoding="utf-8")
    return files


def write_files(root: Path, files: Mapping[str, str]) -> None:
    for rel, content in files.items():
        write_text_lf(root / rel, content)


def copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=_IGNORE)

"""Task loading and structural validation."""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / "tasks"


class TaskError(Exception):
    pass


@dataclass
class Task:
    id: str
    title: str
    dir: Path
    brief: str
    editable: list[str]
    visible_tests: list[str]
    hidden_kind: str  # "pytest" | "mutants" | "none"
    hidden_module: str | None = None
    audit: bool = False
    solvable: bool = True
    max_changed_files: int | None = None
    max_changed_lines: int | None = None
    extra_checks: list[str] = field(default_factory=list)

    @property
    def starter_dir(self) -> Path:
        return self.dir / "starter"

    @property
    def hidden_dir(self) -> Path:
        return self.dir / "hidden"

    @property
    def audit_dir(self) -> Path:
        return self.dir / "audit"

    @property
    def scripted_path(self) -> Path:
        return self.dir / "scripted.py"


def load_task(task_dir: Path) -> Task:
    task_dir = Path(task_dir)
    meta_path = task_dir / "task.json"
    if not meta_path.is_file():
        raise TaskError(f"{task_dir.name}: missing task.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    brief_path = task_dir / "BRIEF.md"
    if not brief_path.is_file():
        raise TaskError(f"{task_dir.name}: missing BRIEF.md")
    hidden = meta.get("hidden", {"kind": "none"})
    return Task(
        id=meta["id"],
        title=meta["title"],
        dir=task_dir,
        brief=brief_path.read_text(encoding="utf-8").strip(),
        editable=list(meta["editable"]),
        visible_tests=list(meta.get("visible_tests", ["tests"])),
        hidden_kind=hidden["kind"],
        hidden_module=hidden.get("module"),
        audit=bool(meta.get("audit", False)),
        solvable=bool(meta.get("solvable", True)),
        max_changed_files=meta.get("max_changed_files"),
        max_changed_lines=meta.get("max_changed_lines"),
        extra_checks=list(meta.get("extra_checks", [])),
    )


def discover_tasks(tasks_dir: Path = TASKS_DIR) -> list[Task]:
    return [load_task(p) for p in sorted(Path(tasks_dir).iterdir()) if (p / "task.json").is_file()]


def get_task(task_id: str, tasks_dir: Path = TASKS_DIR) -> Task:
    for task in discover_tasks(tasks_dir):
        if task.id == task_id or task.id.split("-")[0] == task_id:
            return task
    raise TaskError(f"unknown task: {task_id}")


def load_scenarios(task: Task) -> dict[str, dict]:
    spec = importlib.util.spec_from_file_location(f"scripted_{task.id.replace('-', '_')}", task.scripted_path)
    if spec is None or spec.loader is None:
        raise TaskError(f"{task.id}: cannot load scripted.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SCENARIOS


def structural_problems(task: Task) -> list[str]:
    """Cheap checks that do not execute any scenario."""
    problems: list[str] = []
    if not task.dir.name == task.id:
        problems.append(f"directory name {task.dir.name!r} does not match id {task.id!r}")
    if not (task.starter_dir / "src").is_dir():
        problems.append("starter/src is missing")
    for rel in task.visible_tests:
        if not (task.starter_dir / rel).exists():
            problems.append(f"visible test path starter/{rel} is missing")
    if task.hidden_kind == "pytest" and not list(task.hidden_dir.glob("test_*.py")):
        problems.append("hidden/ has no test_*.py files")
    if task.hidden_kind == "mutants":
        if not list((task.hidden_dir / "mutants").glob("*.py")):
            problems.append("hidden/mutants has no mutant files")
        if not task.hidden_module:
            problems.append("hidden.module is required for mutants")
    if task.audit and not list(task.audit_dir.glob("test_*.py")):
        problems.append("audit is enabled but audit/ has no test_*.py files")
    if not task.scripted_path.is_file():
        problems.append("scripted.py is missing")
    else:
        scenarios = load_scenarios(task)
        for name, scenario in scenarios.items():
            for key in ("weight", "expect", "attempts"):
                if key not in scenario:
                    problems.append(f"scenario {name!r} lacks {key!r}")
        if task.solvable and "correct" not in scenarios:
            problems.append("solvable task needs a 'correct' scenario")
    return problems

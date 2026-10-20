"""Validate tasks: starter must fail, every scripted scenario must end as declared."""

from __future__ import annotations

from pathlib import Path

from loop.checks import evaluate
from loop.providers import make_provider
from loop.runner import DEFAULT_WORK_ROOT, RunConfig, run_task
from loop.task import Task, discover_tasks, load_scenarios, structural_problems
from loop.workspace import create_workspace


def validate_starter_fails(task: Task, work_root: Path) -> list[str]:
    ws = create_workspace(task, work_root / f"validate-{task.id}" / "ws")
    ev = evaluate(task, ws, work_root / f"validate-{task.id}")
    return ["starter already passes all checks; the task is trivial"] if ev.passed else []


def validate_scenario(task: Task, name: str, scenario: dict, tasks_dir: Path, work_root: Path) -> list[str]:
    problems = []
    runs = [("loop", False, scenario["expect"])]
    if "expect_review" in scenario:
        runs.append(("loop-review", True, scenario["expect_review"]))
    for mode, reviewer, expected in runs:
        builder = make_provider("scripted", "builder", tasks_dir, scenario=name)
        reviewer_provider = make_provider("scripted", "reviewer", tasks_dir, scenario=name) if reviewer else None
        config = RunConfig(reviewer=reviewer, work_root=work_root)
        result = run_task(task, builder, config, reviewer_provider, mode=f"validate-{mode}")
        if result.outcome != expected:
            problems.append(f"scenario {name!r} ({mode}): expected {expected!r}, got {result.outcome!r}")
    return problems


def validate_task(task: Task, tasks_dir: Path, work_root: Path = DEFAULT_WORK_ROOT) -> list[str]:
    problems = structural_problems(task)
    if problems:
        return problems
    problems += validate_starter_fails(task, work_root)
    scenarios = load_scenarios(task)
    if not task.solvable and any(s["expect"] == "passed" for s in scenarios.values()):
        problems.append("task is marked unsolvable but a scenario expects success")
    for name, scenario in scenarios.items():
        problems += validate_scenario(task, name, scenario, tasks_dir, work_root)
    return problems


def validate_all(tasks_dir: Path, work_root: Path = DEFAULT_WORK_ROOT) -> dict[str, list[str]]:
    return {t.id: validate_task(t, tasks_dir, work_root) for t in discover_tasks(tasks_dir)}

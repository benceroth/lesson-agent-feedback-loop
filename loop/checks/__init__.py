"""Run every configured check and turn the outcome into feedback for the next attempt."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from loop.checks.base import CheckResult, Failure
from loop.checks.linters import run_mypy, run_ruff
from loop.checks.mutants import run_mutants
from loop.checks.pytest_check import HIDDEN_DIR, run_pytest
from loop.task import Task
from loop.workspace import copy_tree


@dataclass
class Evaluation:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def failures(self) -> list[Failure]:
        return [f for r in self.results for f in r.failures]

    @property
    def visible_failures(self) -> list[Failure]:
        return [f for f in self.failures if not f.hidden]

    @property
    def hidden_failures(self) -> list[Failure]:
        return [f for f in self.failures if f.hidden]

    @property
    def passed(self) -> bool:
        return all(r.ok for r in self.results) and not self.failures

    @property
    def category(self) -> str:
        if self.passed:
            return "ok"
        if any(f.kind == "error" and "tests/" in f.test_id for f in self.visible_failures) or any(
            "SyntaxError" in f.message or "ImportError" in f.message for f in self.failures
        ):
            return "error"
        if self.visible_failures:
            return "visible_failure"
        if self.hidden_failures:
            return "hidden_failure"
        return "check_failure"


def evaluate(task: Task, ws: Path, work_dir: Path, use_hidden: bool = True) -> Evaluation:
    """Run visible, hidden and optional lint/type checks against the workspace."""
    ev = Evaluation()
    targets = list(task.visible_tests)
    if use_hidden and task.hidden_kind == "pytest":
        eval_dir = work_dir / "eval"
        copy_tree(ws, eval_dir)
        hidden_dest = eval_dir / HIDDEN_DIR
        copy_tree(task.hidden_dir, hidden_dest)
        ev.results.append(run_pytest(eval_dir, targets + [HIDDEN_DIR]))
        shutil.rmtree(eval_dir, ignore_errors=True)
    else:
        ev.results.append(run_pytest(ws, targets))
        if use_hidden and task.hidden_kind == "mutants" and ev.results[-1].ok:
            ev.results.append(run_mutants(ws, task.hidden_dir / "mutants", task.hidden_module or "", work_dir))
    for name in task.extra_checks:
        runner = {"ruff": run_ruff, "mypy": run_mypy}[name]
        ev.results.append(runner(ws))
    return ev


def run_audit(task: Task, ws: Path, work_dir: Path) -> bool | None:
    """Ground-truth tests that are never shown to the loop. None when the task has none."""
    if not task.audit:
        return None
    audit_dir = work_dir / "audit"
    copy_tree(ws, audit_dir)
    copy_tree(task.audit_dir, audit_dir / "audit_tests")
    ok = run_pytest(audit_dir, ["audit_tests"], name="audit").ok
    shutil.rmtree(audit_dir, ignore_errors=True)
    return ok


def format_feedback(ev: Evaluation, attempt: int) -> str:
    """Actionable, bounded feedback: failing test names and short errors.

    Hidden test source is never shown; for hidden checks only the name is returned.
    """
    lines = [f"Attempt {attempt} did not pass the automated checks."]
    visible = ev.visible_failures
    if visible:
        lines.append(f"Visible check failures ({len(visible)}):")
        for f in visible[:8]:
            lines.append(f"- {f.test_id}: {f.message}")
            if f.detail:
                lines.append("  " + f.detail.replace("\n", "\n  "))
    hidden = ev.hidden_failures
    if hidden:
        lines.append(f"Hidden acceptance checks failed ({len(hidden)}); their source is not shown:")
        for f in hidden[:8]:
            lines.append(f"- {f.test_id}" if f.kind != "survived" else f"- {f.message}")
    if len(visible) > 8 or len(hidden) > 8:
        lines.append("(further failures omitted)")
    lines.append("Make a focused correction. Do not edit files outside the allowed paths.")
    return "\n".join(lines)

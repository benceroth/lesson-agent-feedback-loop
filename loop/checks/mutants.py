"""Mutation-style hidden check for "write the missing tests" tasks.

The candidate's tests must pass on the real module and fail on every mutant.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from loop.checks.base import CheckResult, Failure
from loop.checks.pytest_check import run_pytest


def run_mutants(workspace: Path, mutants_dir: Path, module: str, work_dir: Path, timeout: float = 60.0) -> CheckResult:
    survivors: list[str] = []
    for mutant in sorted(mutants_dir.glob("*.py")):
        dest = work_dir / f"mutant-{mutant.stem}"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(workspace, dest, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        (dest / module).write_bytes(mutant.read_bytes())
        result = run_pytest(dest, ["tests"], timeout=timeout, name="mutant")
        shutil.rmtree(dest, ignore_errors=True)
        if result.status == "passed":
            survivors.append(mutant.stem)
    failures = [
        Failure(f"mutant::{name}", "survived", f"mutant '{name}' survived: no test failed when the code was broken this way", hidden=True)
        for name in survivors
    ]
    return CheckResult("mutants", "failed" if failures else "passed", failures)

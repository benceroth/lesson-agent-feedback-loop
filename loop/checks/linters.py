"""ruff and mypy adapters. They are skipped (not failed) when the tool is not installed."""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from loop.checks.base import CheckResult, Failure, truncate

_LINT_LINE = re.compile(r"^(?P<loc>[^\s:][^:]*:\d+(?::\d+)?)(?::)?\s+(?P<msg>.+)$")


def run_tool(
    name: str,
    command: Sequence[str],
    cwd: Path,
    kind: str,
    timeout: float = 60.0,
) -> CheckResult:
    try:
        proc = subprocess.run(list(command), cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return CheckResult(name, "error", [Failure(name, "error", f"timed out after {timeout:.0f}s")])
    except FileNotFoundError:
        return CheckResult(name, "skipped", [], f"{name} is not available")
    combined = (proc.stdout + proc.stderr).strip()
    if "No module named" in combined and proc.returncode != 0:
        return CheckResult(name, "skipped", [], f"{name} is not installed")
    if proc.returncode == 0:
        return CheckResult(name, "passed", [], truncate(combined))
    failures = []
    for line in proc.stdout.splitlines():
        match = _LINT_LINE.match(line.strip())
        if match:
            failures.append(Failure(f"{name}:{match['loc']}", kind, truncate(match["msg"], 200)))
    if not failures:
        failures.append(Failure(name, "error", truncate(combined, 300)))
    return CheckResult(name, "failed", failures, truncate(combined, 1500))


def run_ruff(cwd: Path, targets: Sequence[str] = ("src",)) -> CheckResult:
    return run_tool("ruff", [sys.executable, "-m", "ruff", "check", "--output-format", "concise", *targets], cwd, "lint")


def run_mypy(cwd: Path, targets: Sequence[str] = ("src",)) -> CheckResult:
    cmd = [sys.executable, "-m", "mypy", "--no-error-summary", "--ignore-missing-imports", *targets]
    return run_tool("mypy", cmd, cwd, "type")

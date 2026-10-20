"""pytest adapter: run in a subprocess and read structured results from JUnit XML."""

from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from loop.checks.base import CheckResult, Failure, truncate

HIDDEN_DIR = "hidden_tests"


def _test_id(classname: str, name: str) -> str:
    if classname:
        return f"{classname.replace('.', '/')}.py::{name}" if name else classname.replace(".", "/") + ".py"
    return name or "unknown"


def _env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTEST_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_pytest(cwd: Path, targets: list[str], timeout: float = 60.0, name: str = "pytest") -> CheckResult:
    junit = cwd.parent / f"{cwd.name}.junit.xml"
    junit.unlink(missing_ok=True)
    cmd = [
        sys.executable, "-m", "pytest", "-c", "pytest.ini", "--rootdir", ".",
        "-p", "no:cacheprovider", "-q", "--tb=short", f"--junitxml={junit}", *targets,
    ]
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=_env())
    except subprocess.TimeoutExpired:
        return CheckResult(name, "error", [Failure("pytest", "error", f"timed out after {timeout:.0f}s")])
    failures: list[Failure] = []
    if junit.is_file():
        try:
            root = ET.parse(junit).getroot()
        except ET.ParseError:
            root = None
        if root is not None:
            for case in root.iter("testcase"):
                bad = case.find("failure")
                kind = "failure"
                if bad is None:
                    bad = case.find("error")
                    kind = "error"
                if bad is None:
                    continue
                tid = _test_id(case.get("classname", ""), case.get("name", ""))
                failures.append(
                    Failure(tid, kind, truncate(bad.get("message", ""), 200), truncate(bad.text or "", 600), HIDDEN_DIR in tid)
                )
        junit.unlink(missing_ok=True)
    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode == 0:
        return CheckResult(name, "passed", [], truncate(output))
    if not failures:
        message = "no tests were collected" if proc.returncode == 5 else "pytest exited with an error"
        failures.append(Failure("pytest", "error", message, truncate(output), False))
    return CheckResult(name, "failed", failures, truncate(output, 1500))

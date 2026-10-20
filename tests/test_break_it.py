import subprocess
import sys

import pytest

from loop.task import REPO_ROOT


def run_script(name: str) -> str:
    proc = subprocess.run([sys.executable, str(REPO_ROOT / "break-it" / name / "run.py")], capture_output=True, text=True, check=True)
    return proc.stdout


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("no-stop-condition", ["stopped:stalled", "stopped:provider_error"]),
        ("weakened-tests", ["guard_violation", "hidden_failure", "outcome=passed"]),
        ("self-review", ["review_blocked", "audit ok=True", "audit ok=False"]),
    ],
)
def test_break_it_scenarios_show_their_failure(name, expected):
    out = run_script(name)
    for text in expected:
        assert text in out

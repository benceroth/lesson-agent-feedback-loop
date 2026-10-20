"""A builder that weakens the tests: which safeguard is left standing when the allow-list is wrong?"""

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from loop.providers.fake import ScriptedProvider  # noqa: E402
from loop.runner import RunConfig, run_task  # noqa: E402
from loop.task import get_task  # noqa: E402


def main() -> None:
    work_root = Path(__file__).resolve().parents[2] / "runs"
    task = get_task("001")
    leaky = dataclasses.replace(task, editable=[*task.editable, "tests/**"])  # the mistake: tests are writable
    cases = [
        ("correct allow-list, hidden ON ", task, RunConfig(work_root=work_root)),
        ("tests writable,      hidden ON ", leaky, RunConfig(work_root=work_root)),
        ("tests writable,      hidden OFF", leaky, RunConfig(hidden=False, work_root=work_root)),
    ]
    for label, t, config in cases:
        result = run_task(t, ScriptedProvider(scenario="cheater"), config, mode="break-it")
        cats = ",".join(a.category for a in result.attempts)
        print(f"{label}: outcome={result.outcome:<20} attempt categories={cats}")
    print("\nOnly the last row 'passes', and the code was never fixed. Hidden checks are the backstop when the allow-list leaks.")
    if work_root.is_dir() and not any(work_root.iterdir()):
        work_root.rmdir()


if __name__ == "__main__":
    main()

"""A reviewer that is also the builder approves its own blind spot."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from loop.providers.base import ProviderResponse, estimate_tokens  # noqa: E402
from loop.providers.fake import ScriptedProvider  # noqa: E402
from loop.runner import RunConfig, run_task  # noqa: E402
from loop.task import get_task  # noqa: E402


class SelfReviewer(ScriptedProvider):
    """The builder reviewing its own change: it shares the blind spot, so it finds nothing."""

    def complete(self, request):
        if request.role != "reviewer":
            return super().complete(request)
        text = json.dumps({"findings": []})
        return ProviderResponse(text, estimate_tokens(request.system + request.prompt), estimate_tokens(text))


def main() -> None:
    work_root = Path(__file__).resolve().parents[2] / "runs"
    task = get_task("002")
    config = RunConfig(reviewer=True, work_root=work_root)
    cases = [
        ("separate reviewer", ScriptedProvider(scenario="unicode-gap")),
        ("builder reviews itself", SelfReviewer(scenario="unicode-gap")),
    ]
    for label, reviewer in cases:
        result = run_task(task, ScriptedProvider(scenario="unicode-gap"), config, reviewer, mode="break-it")
        cats = ",".join(a.category for a in result.attempts)
        print(f"{label:<24}: outcome={result.outcome:<8} categories={cats:<18} ground-truth audit ok={result.audit_ok}")
    print("\nThe self-reviewer approves a change the ground-truth audit rejects (false confidence).")
    if work_root.is_dir() and not any(work_root.iterdir()):
        work_root.rmdir()


if __name__ == "__main__":
    main()

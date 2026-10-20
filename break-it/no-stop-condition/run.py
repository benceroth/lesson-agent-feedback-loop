"""A loop with no stop condition keeps paying for attempts that go nowhere."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from loop.budget import Budget  # noqa: E402
from loop.providers.base import ProviderError, ProviderResponse, estimate_tokens  # noqa: E402
from loop.runner import RunConfig, run_task  # noqa: E402
from loop.task import get_task  # noqa: E402

PLUG = 12  # this demo cuts the provider off after 12 calls; a real unbounded loop would not stop


class AlwaysWrong:
    """Every attempt is a different wrong answer, so the failure count never improves."""

    name = "always-wrong"
    model = "scripted-demo"

    def __init__(self, limit: int | None = None):
        self.limit = limit
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        if self.limit is not None and self.calls > self.limit:
            raise ProviderError("demo plug pulled: the loop would have kept going")
        code = f"def paginate(items, page, page_size):\n    start = page * page_size + {self.calls}\n    return list(items[start:start + page_size])\n"
        text = json.dumps({"summary": f"try offset {self.calls}", "files": {"src/pagination.py": code}})
        return ProviderResponse(text, estimate_tokens(request.system + request.prompt), estimate_tokens(text))

    def info(self):
        return {}


def run(label: str, budget: Budget, limit: int | None, work_root: Path) -> None:
    provider = AlwaysWrong(limit)
    result = run_task(get_task("001"), provider, RunConfig(budget=budget, work_root=work_root), mode="break-it")
    print(f"{label}: outcome={result.outcome:<24} attempts={len(result.attempts):<3} tokens~{result.tokens}")


def main() -> None:
    work_root = Path(__file__).resolve().parents[2] / "runs"
    run("default budget          ", Budget(), None, work_root)
    unbounded = Budget(max_attempts=10**9, max_seconds=1e9, max_tokens=10**12, patience=10**9)
    run("no stop condition (cut) ", unbounded, PLUG, work_root)
    print(f"\nWithout limits the second run only ended because this demo cut it off after {PLUG} calls.")
    if work_root.is_dir() and not any(work_root.iterdir()):
        work_root.rmdir()


if __name__ == "__main__":
    main()

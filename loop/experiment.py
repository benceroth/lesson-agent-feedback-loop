"""Run the single-shot vs loop experiment and write CSVs, an SVG chart and a markdown report."""

from __future__ import annotations

import json
import platform
from collections.abc import Callable
from datetime import date
from pathlib import Path

from loop.budget import Budget
from loop.chart import grouped_bar_svg
from loop.metrics import (
    DETERMINISTIC_COLUMNS,
    MODE_ORDER,
    RUN_COLUMNS,
    SUMMARY_COLUMNS,
    failure_categories,
    read_csv,
    stop_reasons,
    summarize,
    write_csv,
)
from loop.providers import make_provider
from loop.runner import DEFAULT_WORK_ROOT, RunConfig, RunResult, run_task
from loop.task import TASKS_DIR, discover_tasks

LOOP_MAX_ATTEMPTS = 4


def mode_config(mode: str, work_root: Path) -> RunConfig:
    budget = Budget(max_attempts=1 if mode == "single-shot" else LOOP_MAX_ATTEMPTS)
    return RunConfig(budget=budget, reviewer=(mode == "loop-review"), work_root=work_root)


def run_experiment(
    provider_kind: str = "scripted",
    runs: int = 10,
    seed: int = 20261020,
    task_ids: list[str] | None = None,
    modes: list[str] | None = None,
    tasks_dir: Path = TASKS_DIR,
    work_root: Path = DEFAULT_WORK_ROOT,
    progress: Callable[[str], None] | None = None,
) -> list[RunResult]:
    modes = modes or list(MODE_ORDER)
    tasks = [t for t in discover_tasks(tasks_dir) if not task_ids or t.id in task_ids or t.id.split("-")[0] in task_ids]
    results: list[RunResult] = []
    for task in tasks:
        for i in range(runs):
            for mode in modes:
                builder = make_provider(provider_kind, "builder", tasks_dir, seed, i)
                reviewer = make_provider(provider_kind, "reviewer", tasks_dir, seed, i) if mode == "loop-review" else None
                result = run_task(task, builder, mode_config(mode, work_root), reviewer, mode=mode, run_index=i, seed=seed)
                results.append(result)
            if progress:
                progress(f"{task.id} run {i + 1}/{runs}")
    return results


def _pct(value: object) -> str:
    return f"{float(value):.0%}" if value != "" else "n/a"


def _num(value: object) -> str:
    return f"{float(value):g}" if value != "" else "n/a"


def render_markdown(summary: list[dict], categories: list[dict], stops: list[dict], provenance: dict) -> str:
    label = (
        "**Scripted demo, not a model benchmark.** The replies come from canned scenarios (see `tasks/*/scripted.py`) "
        "chosen by a seeded random generator, so these numbers show how the harness measures a loop, not how any model performs."
        if provenance["provider"] == "scripted"
        else f"Real-model run: model `{provenance['model']}`, {provenance['date']}, N={provenance['runs']} per task per mode. A teaching experiment, not a benchmark."
    )
    lines = [
        "# Experiment results",
        "",
        label,
        "",
        f"- Provider: `{provenance['provider']}` (model: `{provenance['model']}`)",
        f"- Date: {provenance['date']}",
        f"- Runs per task per mode (N): {provenance['runs']}; seed: {provenance['seed']}",
        f"- Loop budget: {provenance['loop_max_attempts']} attempts, stall patience 2; single-shot = 1 attempt",
        "- Token figures are a proxy (about 4 characters per token), not billed tokens.",
        "",
        "## Pass rates and cost proxy",
        "",
        "| Task | Mode | N | pass@1 | pass within budget | attempts / success | tokens / success | false confidence | stalled | budget stops |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in summary:
        lines.append(
            f"| {r['task']} | {r['mode']} | {r['n']} | {_pct(r['pass_at_1'])} | {_pct(r['pass_within_budget'])} | "
            f"{_num(r['attempts_per_success'])} | {_num(r['tokens_per_success'])} | {r['false_confidence']} | {r['stopped_stalled']} | {r['stopped_budget']} |"
        )
    lines += [
        "",
        "`false confidence` = runs that passed the loop's own checks but failed a ground-truth audit that the loop never sees.",
        "`attempts / success` and `tokens / success` divide the total spent across all runs, including failed runs, by the number of successes.",
        "",
        "## Failing attempts by category",
        "",
        "| Mode | Category | Attempts |",
        "|---|---|---:|",
    ]
    lines += [f"| {r['mode']} | {r['category']} | {r['attempts']} |" for r in categories]
    lines += ["", "## How runs ended", "", "| Mode | Outcome | Runs |", "|---|---|---:|"]
    lines += [f"| {r['mode']} | {r['outcome']} | {r['runs']} |" for r in stops]
    lines += [
        "",
        "![pass rates](pass-rate.svg)",
        "",
        "![cost proxy](cost.svg)",
        "",
        "With a small N, differences of a few runs are noise. Read the protocol in `experiments/single-shot-vs-loop.md` before drawing conclusions.",
        "",
    ]
    return "\n".join(lines)


def write_report(rows: list[dict], out_dir: Path, provenance: dict) -> None:
    summary = summarize(rows)
    write_csv(out_dir / "summary.csv", summary, SUMMARY_COLUMNS)
    categories = failure_categories(rows)
    write_csv(out_dir / "failure-categories.csv", categories, ["mode", "category", "attempts"])
    stops = stop_reasons(rows)
    modes = [m for m in MODE_ORDER if any(r["mode"] == m for r in summary)]
    task_names = sorted({r["task"] for r in summary if r["task"] != "ALL"}) + ["ALL"]
    index = {(r["task"], r["mode"]): r for r in summary}

    def series(field: str, scale: float = 1.0) -> dict[str, list[float | None]]:
        return {
            m: [None if index[(t, m)][field] == "" else float(index[(t, m)][field]) * scale for t in task_names]
            for m in modes
        }

    n = provenance["runs"]
    sub = f"{provenance['provider']} / {provenance['model']} - N={n} per task per mode - {provenance['date']}"
    if provenance["provider"] == "scripted":
        sub += " - SCRIPTED DEMO, NOT A MODEL BENCHMARK"
    (out_dir / "pass-rate.svg").write_text(
        grouped_bar_svg("Pass within budget by task and mode", sub, task_names, series("pass_within_budget"), 1.0, "{:.0%}", "runs that passed all checks"),
        encoding="utf-8", newline="\n",
    )
    cost = series("mean_tokens")
    top = max((v for vals in cost.values() for v in vals if v is not None), default=1.0)
    (out_dir / "cost.svg").write_text(
        grouped_bar_svg("Mean cost proxy per run (tokens, ~4 chars each)", sub, task_names, cost, top * 1.1, "{:,.0f}", "tokens per run"),
        encoding="utf-8", newline="\n",
    )
    (out_dir / "summary.md").write_text(render_markdown(summary, categories, stops, provenance), encoding="utf-8", newline="\n")


def make_provenance(provider: str, model: str, runs: int, seed: int, tasks: list[str]) -> dict:
    return {
        "provider": provider,
        "model": model,
        "date": date.today().isoformat(),
        "runs": runs,
        "seed": seed,
        "tasks": tasks,
        "modes": MODE_ORDER,
        "loop_max_attempts": LOOP_MAX_ATTEMPTS,
        "python": platform.python_version(),
        "command": f"python -m loop experiment --provider {provider} --runs {runs} --seed {seed}",
        "note": "Scripted provider results are a harness demo, not a model benchmark." if provider == "scripted" else "Teaching experiment, not a benchmark.",
    }


def save_experiment(results: list[RunResult], out_dir: Path, provenance: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [r.to_row() for r in results]
    write_csv(out_dir / "runs.csv", rows, RUN_COLUMNS)
    with (out_dir / "attempts.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for r in results:
            data = r.to_dict()
            data["wall_seconds"] = round(data["wall_seconds"], 2)
            handle.write(json.dumps(data, sort_keys=True) + "\n")
    (out_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_report(read_csv(out_dir / "runs.csv"), out_dir, provenance)


TOKEN_TOLERANCE = 0.05


def _within_tolerance(fresh: object, committed: object) -> bool:
    # The token proxy counts pytest output, whose wording and paths differ by OS and Python version.
    try:
        old = float(committed)
        return abs(float(fresh) - old) <= TOKEN_TOLERANCE * max(old, 1.0)
    except (TypeError, ValueError):
        return False


def verify_results(results_dir: Path, work_root: Path = DEFAULT_WORK_ROOT, tasks_dir: Path = TASKS_DIR) -> list[str]:
    """Re-run the committed scripted experiment and report any deterministic difference."""
    provenance = json.loads((results_dir / "provenance.json").read_text(encoding="utf-8"))
    if provenance["provider"] != "scripted":
        return ["only scripted results can be re-verified"]
    fresh = [r.to_row() for r in run_experiment("scripted", provenance["runs"], provenance["seed"], provenance["tasks"], tasks_dir=tasks_dir, work_root=work_root)]
    committed = read_csv(results_dir / "runs.csv")
    if len(fresh) != len(committed):
        return [f"row count differs: committed {len(committed)}, fresh {len(fresh)}"]
    problems = []
    for new, old in zip(fresh, committed, strict=True):
        for col in DETERMINISTIC_COLUMNS:
            if col == "tokens" and _within_tolerance(new[col], old[col]):
                continue
            if str(new[col]) != str(old[col]):
                problems.append(f"{old['task']} {old['mode']} run {old['run']}: {col} committed={old[col]!r} fresh={new[col]!r}")
    return problems

"""Metrics: per (task, mode) summary tables from run rows."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Sequence

RUN_COLUMNS = [
    "task", "mode", "run", "seed", "provider", "model", "scenario", "outcome",
    "passed", "pass_at_1", "attempts", "tokens", "wall_seconds", "audit_ok", "categories",
]
DETERMINISTIC_COLUMNS = [c for c in RUN_COLUMNS if c != "wall_seconds"]
SUMMARY_COLUMNS = [
    "task", "mode", "n", "pass_at_1", "pass_within_budget", "mean_attempts", "attempts_per_success",
    "mean_tokens", "tokens_per_success", "false_confidence", "stopped_stalled", "stopped_budget",
]
MODE_ORDER = ["single-shot", "loop", "loop-review"]


def write_csv(path: Path, rows: Iterable[dict], columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _ratio(num: float, den: float) -> float | str:
    return round(num / den, 3) if den else ""


def _summarize_group(task: str, mode: str, rows: list[dict]) -> dict:
    n = len(rows)
    successes = [r for r in rows if int(r["passed"])]
    total_attempts = sum(int(r["attempts"]) for r in rows)
    total_tokens = sum(int(r["tokens"]) for r in rows)
    return {
        "task": task,
        "mode": mode,
        "n": n,
        "pass_at_1": _ratio(sum(int(r["pass_at_1"]) for r in rows), n),
        "pass_within_budget": _ratio(len(successes), n),
        "mean_attempts": _ratio(total_attempts, n),
        "attempts_per_success": _ratio(total_attempts, len(successes)),
        "mean_tokens": round(total_tokens / n) if n else "",
        "tokens_per_success": round(total_tokens / len(successes)) if successes else "",
        # passed the loop's own checks but failed the ground-truth audit
        "false_confidence": sum(1 for r in successes if str(r["audit_ok"]) == "0"),
        "stopped_stalled": sum(1 for r in rows if r["outcome"] == "stopped:stalled"),
        "stopped_budget": sum(1 for r in rows if r["outcome"] in ("stopped:max_attempts", "stopped:max_seconds", "stopped:max_tokens")),
    }


def summarize(rows: list[dict]) -> list[dict]:
    """One row per (task, mode), plus an ALL row per mode. Rows must be CSV-shaped dicts."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_mode: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["task"], row["mode"])].append(row)
        by_mode[row["mode"]].append(row)
    order = {m: i for i, m in enumerate(MODE_ORDER)}
    out = [_summarize_group(t, m, g) for (t, m), g in sorted(groups.items(), key=lambda kv: (kv[0][0], order.get(kv[0][1], 99)))]
    out += [_summarize_group("ALL", m, by_mode[m]) for m in sorted(by_mode, key=lambda m: order.get(m, 99))]
    return out


def failure_categories(rows: list[dict]) -> list[dict]:
    """Count failing attempt categories per mode (every non-ok attempt)."""
    counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        for category in str(row["categories"]).split("|"):
            if category and category != "ok":
                counts[row["mode"]][category] += 1
    order = {m: i for i, m in enumerate(MODE_ORDER)}
    return [
        {"mode": mode, "category": cat, "attempts": count}
        for mode in sorted(counts, key=lambda m: order.get(m, 99))
        for cat, count in sorted(counts[mode].items())
    ]


def stop_reasons(rows: list[dict]) -> list[dict]:
    counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        counts[row["mode"]][row["outcome"]] += 1
    order = {m: i for i, m in enumerate(MODE_ORDER)}
    return [
        {"mode": mode, "outcome": outcome, "runs": count}
        for mode in sorted(counts, key=lambda m: order.get(m, 99))
        for outcome, count in sorted(counts[mode].items())
    ]

"""Command line: run one task, validate tasks, run the experiment, demo the guard."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from loop.budget import Budget
from loop.experiment import make_provenance, run_experiment, save_experiment, verify_results, write_report
from loop.metrics import MODE_ORDER, read_csv
from loop.providers import PROVIDER_KINDS, make_provider
from loop.providers.base import ProviderError
from loop.runner import DEFAULT_WORK_ROOT, RunConfig, run_task
from loop.task import REPO_ROOT, TASKS_DIR, TaskError, get_task
from loop.validate import validate_all


def _cleanup(work_root: Path) -> None:
    if work_root.is_dir() and not any(work_root.iterdir()):
        work_root.rmdir()


def _cmd_run(args: argparse.Namespace) -> int:
    task = get_task(args.task, args.tasks_dir)
    mode = args.mode
    budget = Budget(
        max_attempts=1 if mode == "single-shot" else args.max_attempts,
        max_seconds=args.max_seconds,
        max_tokens=args.max_tokens,
    )
    config = RunConfig(
        budget=budget, guard=not args.no_guard, hidden=not args.no_hidden,
        reviewer=(mode == "loop-review"), keep_workspace=args.keep, work_root=args.work_root,
    )
    builder = make_provider(args.provider, "builder", args.tasks_dir, args.seed, args.run_index, args.scenario)
    reviewer = None
    if config.reviewer:
        reviewer = make_provider(args.provider, "reviewer", args.tasks_dir, args.seed, args.run_index, args.scenario)
    result = run_task(task, builder, config, reviewer, mode=mode, run_index=args.run_index, seed=args.seed, log=print)
    print(f"\n{task.id}: {result.outcome} after {len(result.attempts)} attempt(s), ~{result.tokens} tokens (proxy)")
    if result.scenario:
        print(f"scripted scenario: {result.scenario}")
    if result.audit_ok is False:
        print("WARNING: passed the loop's checks but failed the ground-truth audit (false confidence).")
    if result.escalation:
        print("\n" + result.escalation)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    _cleanup(args.work_root)
    return 0 if result.passed else 1


def _cmd_validate(args: argparse.Namespace) -> int:
    outcome = validate_all(args.tasks_dir, args.work_root)
    bad = 0
    for task_id, problems in outcome.items():
        print(f"{'ok  ' if not problems else 'FAIL'} {task_id}")
        for p in problems:
            print(f"     - {p}")
        bad += bool(problems)
    for leftover in args.work_root.glob("validate-*") if args.work_root.is_dir() else []:
        shutil.rmtree(leftover, ignore_errors=True)
    _cleanup(args.work_root)
    return 1 if bad else 0


def _cmd_experiment(args: argparse.Namespace) -> int:
    results = run_experiment(args.provider, args.runs, args.seed, args.tasks, args.modes, args.tasks_dir, args.work_root, progress=print)
    model = results[0].model if results else "unknown"
    task_ids = sorted({r.task_id for r in results})
    save_experiment(results, args.out, make_provenance(args.provider, model, args.runs, args.seed, task_ids))
    print(f"wrote results to {args.out}")
    _cleanup(args.work_root)
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    provenance = json.loads((args.results / "provenance.json").read_text(encoding="utf-8"))
    write_report(read_csv(args.results / "runs.csv"), args.results, provenance)
    print(f"regenerated report in {args.results}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    problems = verify_results(args.results, args.work_root, args.tasks_dir)
    for p in problems:
        print("MISMATCH", p)
    print("committed results reproduce exactly" if not problems else f"{len(problems)} difference(s)")
    _cleanup(args.work_root)
    return 1 if problems else 0


def _cmd_guard_demo(args: argparse.Namespace) -> int:
    """Task 001, scripted 'cheater' scenario that edits the visible tests instead of the code."""
    task = get_task("001", args.tasks_dir)
    cases = [
        ("guard ON,  hidden checks ON ", RunConfig(work_root=args.work_root)),
        ("guard OFF, hidden checks ON ", RunConfig(guard=False, work_root=args.work_root)),
        ("guard OFF, hidden checks OFF", RunConfig(guard=False, hidden=False, work_root=args.work_root)),
    ]
    for label, config in cases:
        provider = make_provider("scripted", "builder", args.tasks_dir, scenario="cheater")
        result = run_task(task, provider, config, mode="guard-demo")
        cats = ",".join(a.category for a in result.attempts)
        print(f"{label}: outcome={result.outcome:<22} attempt categories={cats}")
    print("\nOnly the last row 'passes', and it is a lie: the tests were edited, not the code. Guard and hidden checks each catch it.")
    _cleanup(args.work_root)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m loop", description="Feedback-loop lab (teaching experiment, not a benchmark).")
    parser.add_argument("--tasks-dir", type=Path, default=TASKS_DIR)
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT, help="scratch folder for workspaces (git-ignored)")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run one task")
    run.add_argument("task", help="task id or number, e.g. 001")
    run.add_argument("--provider", choices=PROVIDER_KINDS, default="scripted")
    run.add_argument("--mode", choices=MODE_ORDER, default="loop")
    run.add_argument("--scenario", help="scripted provider only: force a scenario")
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--run-index", type=int, default=0)
    run.add_argument("--max-attempts", type=int, default=4)
    run.add_argument("--max-seconds", type=float, default=300.0)
    run.add_argument("--max-tokens", type=int, default=60_000)
    run.add_argument("--no-guard", action="store_true", help="demonstration only")
    run.add_argument("--no-hidden", action="store_true", help="demonstration only")
    run.add_argument("--keep", action="store_true", help="keep the workspace under --work-root")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=_cmd_run)

    sub.add_parser("validate-tasks", help="check starters fail and scripted scenarios end as declared").set_defaults(func=_cmd_validate)

    exp = sub.add_parser("experiment", help="single-shot vs loop over all tasks")
    exp.add_argument("--provider", choices=PROVIDER_KINDS, default="scripted")
    exp.add_argument("--runs", type=int, default=10)
    exp.add_argument("--seed", type=int, default=20261020)
    exp.add_argument("--tasks", nargs="*")
    exp.add_argument("--modes", nargs="*", choices=MODE_ORDER)
    exp.add_argument("--out", type=Path, default=REPO_ROOT / "experiments" / "results")
    exp.set_defaults(func=_cmd_experiment)

    rep = sub.add_parser("report", help="regenerate summary/chart from runs.csv")
    rep.add_argument("--results", type=Path, default=REPO_ROOT / "experiments" / "results")
    rep.set_defaults(func=_cmd_report)

    ver = sub.add_parser("verify-results", help="re-run committed scripted results and compare")
    ver.add_argument("--results", type=Path, default=REPO_ROOT / "experiments" / "results")
    ver.set_defaults(func=_cmd_verify)

    sub.add_parser("guard-demo", help="show the reward-hacking guard catching a cheating attempt").set_defaults(func=_cmd_guard_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (TaskError, ProviderError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

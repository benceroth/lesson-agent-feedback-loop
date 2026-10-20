"""The loop: attempt -> guard -> checks -> (reviewer) -> structured feedback -> retry within budget."""

from __future__ import annotations

import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from loop.budget import Budget, BudgetTracker, ProgressTracker
from loop.checks import Evaluation, evaluate, format_feedback, run_audit
from loop.guard import Guard
from loop.providers.base import Provider, ProviderError, ProviderRequest, ReplyError, parse_builder_reply
from loop.reviewer import format_review_feedback, review
from loop.task import REPO_ROOT, Task
from loop.workspace import create_workspace, read_files, write_files

DEFAULT_WORK_ROOT = REPO_ROOT / "runs"

BUILDER_SYSTEM = """You are the builder in an automated feedback loop.
Change only the allowed paths. Automated checks (some hidden) decide whether you are done, not your confidence.
Reply with ONE JSON object and nothing else:
{"summary": "<what you changed and why, one or two sentences>", "files": {"<relative path>": "<complete new file content>"}}
If you believe the requirements cannot be satisfied, say so in "summary" and return an empty "files" object."""


@dataclass(frozen=True)
class RunConfig:
    budget: Budget = field(default_factory=Budget)
    guard: bool = True
    hidden: bool = True
    reviewer: bool = False
    keep_workspace: bool = False
    work_root: Path = DEFAULT_WORK_ROOT


@dataclass
class AttemptRecord:
    attempt: int
    category: str
    accepted: bool
    failures: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    tokens: int = 0
    summary: str = ""


@dataclass
class RunResult:
    task_id: str
    mode: str
    run_index: int
    seed: int
    provider: str
    model: str
    scenario: str
    outcome: str  # passed | stopped:<reason>
    attempts: list[AttemptRecord]
    tokens: int
    wall_seconds: float
    audit_ok: bool | None
    escalation: str

    @property
    def passed(self) -> bool:
        return self.outcome == "passed"

    @property
    def pass_at_1(self) -> bool:
        return bool(self.attempts) and self.attempts[0].accepted

    def to_dict(self) -> dict:
        data = asdict(self)
        data["passed"] = self.passed
        data["pass_at_1"] = self.pass_at_1
        return data

    def to_row(self) -> dict:
        return {
            "task": self.task_id,
            "mode": self.mode,
            "run": self.run_index,
            "seed": self.seed,
            "provider": self.provider,
            "model": self.model,
            "scenario": self.scenario,
            "outcome": self.outcome,
            "passed": int(self.passed),
            "pass_at_1": int(self.pass_at_1),
            "attempts": len(self.attempts),
            "tokens": self.tokens,
            "wall_seconds": round(self.wall_seconds, 2),
            "audit_ok": "" if self.audit_ok is None else int(self.audit_ok),
            "categories": "|".join(a.category for a in self.attempts),
        }


def build_builder_prompt(task: Task, files: dict[str, str], feedback: str | None, attempt: int) -> str:
    parts = [f"# Task: {task.title}", task.brief, "## Allowed paths", "\n".join(f"- {p}" for p in task.editable), "## Current files"]
    for path, content in files.items():
        parts.append(f"### {path}\n```python\n{content.rstrip()}\n```")
    if feedback:
        parts += [f"## Feedback on attempt {attempt - 1}", feedback]
    return "\n\n".join(parts)


def build_escalation(task: Task, outcome: str, attempts: list[AttemptRecord]) -> str:
    """A hand-back message: report the failure honestly instead of claiming success."""
    reason = outcome.split(":", 1)[1] if ":" in outcome else outcome
    last = attempts[-1] if attempts else None
    lines = [
        f"ESCALATION - human decision needed for task {task.id}.",
        f"The loop stopped without a passing result (reason: {reason}) after {len(attempts)} attempt(s).",
    ]
    if last and last.failures:
        lines.append("Still failing: " + ", ".join(last.failures[:5]))
    if last and last.violations:
        lines.append("Last attempt was rejected by the guard: " + "; ".join(last.violations[:3]))
    if reason == "stalled":
        lines.append("Attempts stopped getting closer to passing. The brief or the checks may be contradictory or wrong.")
    lines.append("Not retrying automatically. Suggested next step: read the attempt log, then fix the spec or the checks, or do the change by hand.")
    return "\n".join(lines)


def run_task(
    task: Task,
    provider: Provider,
    config: RunConfig = RunConfig(),
    reviewer_provider: Provider | None = None,
    mode: str = "loop",
    run_index: int = 0,
    seed: int = 0,
    clock: Callable[[], float] = time.monotonic,
    log: Callable[[str], None] | None = None,
) -> RunResult:
    if config.reviewer and reviewer_provider is None:
        raise ValueError("reviewer=True requires a separate reviewer_provider")
    say = log or (lambda _msg: None)
    label = f"{task.id}-{mode}-{run_index:03d}"
    ws = create_workspace(task, config.work_root / label / "ws")
    scratch = config.work_root / label
    guard = Guard(task.editable, task.max_changed_files, task.max_changed_lines)
    protected = guard.snapshot_protected(ws)
    tracker = BudgetTracker(config.budget, clock)
    progress = ProgressTracker(config.budget.patience)
    records: list[AttemptRecord] = []
    feedback: str | None = None
    outcome = ""

    try:
        while True:
            reason = tracker.exhausted()
            if reason:
                outcome = f"stopped:{reason}"
                break
            if progress.stalled:
                outcome = "stopped:stalled"
                break
            tracker.start_attempt()
            n = tracker.attempts
            record = AttemptRecord(n, "", False)
            records.append(record)
            request = ProviderRequest("builder", task.id, n, BUILDER_SYSTEM, build_builder_prompt(task, read_files(ws), feedback, n))
            try:
                reply = provider.complete(request)
            except ProviderError as exc:
                record.category = "provider_error"
                record.summary = str(exc)
                outcome = "stopped:provider_error"
                break
            record.tokens += reply.tokens_in + reply.tokens_out
            tracker.add_tokens(record.tokens)
            try:
                files, record.summary = parse_builder_reply(reply.text)
            except ReplyError as exc:
                record.category = "malformed_reply"
                feedback = f"Your reply could not be used: {exc}. Reply with a single JSON object as specified."
                progress.update(None)
                say(f"attempt {n}: malformed reply")
                continue
            record.summary = record.summary[:200]
            if not files:
                record.category = "empty_response"
                feedback = "You returned no file changes. Return the complete new content of every file you change."
                progress.update(None)
                say(f"attempt {n}: empty response")
                continue
            if config.guard:
                current = {p: (ws / p).read_text(encoding="utf-8") if (ws / p).is_file() else "" for p in files}
                violations = guard.check_proposal(files, current)
                if violations:
                    record.category = "guard_violation"
                    record.violations = [str(v) for v in violations]
                    feedback = (
                        "Your change was rejected before it was applied:\n"
                        + "\n".join(f"- {v}" for v in violations)
                        + "\nTests and configuration are protected. Fix the implementation instead."
                    )
                    progress.update(None)
                    say(f"attempt {n}: guard violation")
                    continue
            write_files(ws, files)
            if config.guard:
                leaked = guard.verify_protected(ws, protected)
                if leaked:
                    record.category = "guard_violation"
                    record.violations = [str(v) for v in leaked]
                    outcome = "stopped:guard_violation"
                    break
            ev = evaluate(task, ws, scratch, use_hidden=config.hidden)
            record.failures = [f.test_id for f in ev.failures]
            if ev.passed:
                record.category = "ok"
                accepted, feedback = _review_gate(config, reviewer_provider, task, ws, n, ev, record, tracker)
                record.accepted = accepted
                if accepted:
                    outcome = "passed"
                    break
                progress.update(len(record.findings) or 1)
            else:
                record.category = ev.category
                feedback = format_feedback(ev, n)
                progress.update(len(ev.failures))
            say(f"attempt {n}: {record.category} ({len(record.failures) or len(record.findings)} issue(s))")
        audit_ok = run_audit(task, ws, scratch) if outcome == "passed" else None
    finally:
        if not config.keep_workspace:
            shutil.rmtree(scratch, ignore_errors=True)

    info = provider.info().get("scenarios", {})
    return RunResult(
        task_id=task.id,
        mode=mode,
        run_index=run_index,
        seed=seed,
        provider=provider.name,
        model=provider.model,
        scenario=str(info.get(task.id, "")),
        outcome=outcome,
        attempts=records,
        tokens=tracker.tokens,
        wall_seconds=tracker.elapsed,
        audit_ok=audit_ok,
        escalation="" if outcome == "passed" else build_escalation(task, outcome, records),
    )


def _review_gate(
    config: RunConfig,
    reviewer_provider: Provider | None,
    task: Task,
    ws: Path,
    attempt: int,
    ev: Evaluation,
    record: AttemptRecord,
    tracker: BudgetTracker,
) -> tuple[bool, str | None]:
    if not config.reviewer or reviewer_provider is None:
        return True, None
    summary = "visible checks: passed\nhidden acceptance checks: " + ("passed" if config.hidden else "not run")
    try:
        result = review(reviewer_provider, task, ws, attempt, summary)
    except ProviderError as exc:
        record.category = "provider_error"
        return False, f"The reviewer could not run: {exc}"
    record.tokens += result.tokens
    tracker.add_tokens(result.tokens)
    record.findings = [f.render() for f in result.findings]
    if result.approved:
        return True, None
    record.category = "review_blocked"
    record.findings = [f.render() for f in result.blocking] or ["malformed reviewer reply"]
    return False, format_review_feedback(result)

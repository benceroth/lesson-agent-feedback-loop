"""Separate, read-only reviewer role.

The reviewer is a different provider instance with its own prompt
(templates/review-prompt.md). It sees the brief, the diff and a summary of the
check outcomes, but never the builder's reasoning or summary. It cannot change
files: any edits in its reply are ignored and counted. Findings without
evidence are demoted, because a reviewer should show, not assert.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path

from loop.providers.base import Provider, ProviderRequest, ReplyError, extract_json
from loop.task import REPO_ROOT, Task

SEVERITIES = ("blocker", "major", "minor", "nit")
BLOCKING = {"blocker", "major"}
REVIEW_TEMPLATE = REPO_ROOT / "templates" / "review-prompt.md"


@dataclass(frozen=True)
class Finding:
    severity: str
    category: str
    file: str
    line: int | None
    claim: str
    evidence: str
    demoted: bool = False

    @property
    def blocking(self) -> bool:
        return self.severity in BLOCKING

    def render(self) -> str:
        where = f"{self.file}:{self.line}" if self.line else self.file
        return f"[{self.severity}/{self.category}] {where} - {self.claim} (evidence: {self.evidence})"


@dataclass
class ReviewResult:
    findings: list[Finding] = field(default_factory=list)
    tokens: int = 0
    ignored_edits: int = 0
    malformed: bool = False

    @property
    def blocking(self) -> list[Finding]:
        return [f for f in self.findings if f.blocking]

    @property
    def approved(self) -> bool:
        return not self.malformed and not self.blocking


def parse_findings(text: str) -> tuple[list[Finding], int]:
    """Parse the findings schema. Returns (findings, number_of_ignored_file_edits)."""
    data = extract_json(text)
    raw = data.get("findings")
    if not isinstance(raw, list):
        raise ReplyError("'findings' must be a list")
    findings: list[Finding] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ReplyError("each finding must be an object")
        severity = str(item.get("severity", "")).lower()
        if severity not in SEVERITIES:
            raise ReplyError(f"unknown severity {severity!r}")
        evidence = str(item.get("evidence", "")).strip()
        demoted = False
        if severity in BLOCKING and not evidence:
            severity, demoted = "nit", True
        line = item.get("line")
        findings.append(
            Finding(
                severity=severity,
                category=str(item.get("category", "other")),
                file=str(item.get("file", "")),
                line=line if isinstance(line, int) else None,
                claim=str(item.get("claim", "")).strip(),
                evidence=evidence,
                demoted=demoted,
            )
        )
    edits = data.get("files")
    return findings, len(edits) if isinstance(edits, dict) else 0


def diff_against_starter(task: Task, ws: Path) -> str:
    """Unified diff of every Python file that differs from the starter."""
    chunks: list[str] = []
    names = {p.relative_to(task.starter_dir).as_posix() for p in task.starter_dir.rglob("*.py")}
    names |= {p.relative_to(ws).as_posix() for p in ws.rglob("*.py") if "__pycache__" not in p.parts}
    for name in sorted(names):
        old_path, new_path = task.starter_dir / name, ws / name
        old = old_path.read_text(encoding="utf-8").splitlines() if old_path.is_file() else []
        new = new_path.read_text(encoding="utf-8").splitlines() if new_path.is_file() else []
        chunks.extend(difflib.unified_diff(old, new, f"a/{name}", f"b/{name}", lineterm=""))
    return "\n".join(chunks) or "(no changes)"


def load_review_system() -> str:
    return REVIEW_TEMPLATE.read_text(encoding="utf-8").strip()


def review(provider: Provider, task: Task, ws: Path, attempt: int, check_summary: str) -> ReviewResult:
    prompt = "\n\n".join(
        [
            f"# Task: {task.title}",
            task.brief,
            "## Proposed change (unified diff)",
            "```diff\n" + diff_against_starter(task, ws) + "\n```",
            "## Automated check summary",
            check_summary,
        ]
    )
    response = provider.complete(ProviderRequest("reviewer", task.id, attempt, load_review_system(), prompt))
    tokens = response.tokens_in + response.tokens_out
    try:
        findings, ignored = parse_findings(response.text)
    except ReplyError:
        return ReviewResult(tokens=tokens, malformed=True)
    return ReviewResult(findings, tokens, ignored)


def format_review_feedback(result: ReviewResult) -> str:
    if result.malformed:
        return "The reviewer reply was malformed, so the change could not be approved."
    lines = ["The independent reviewer rejected the change. Blocking findings:"]
    lines += [f"- {f.render()}" for f in result.blocking]
    lines.append("Address each finding with a focused change.")
    return "\n".join(lines)

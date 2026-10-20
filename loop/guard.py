"""Reward-hacking guard: an allow-list of editable paths plus diff-scope limits.

Only paths matching ``editable`` globs may change. Everything else (tests,
config, hidden checks) is protected, so the loop cannot "pass" by editing the
judge. See docs/safeguards.md.
"""

from __future__ import annotations

import difflib
import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Violation:
    path: str
    rule: str  # protected_path | unsafe_path | diff_scope | modified_protected
    detail: str

    def __str__(self) -> str:
        return f"{self.rule}: {self.path} - {self.detail}"


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(f"^{out}$")


def normalize_path(path: str) -> str | None:
    """Return a safe relative POSIX path, or None if the path is unsafe."""
    p = path.replace("\\", "/")
    if not p or p.startswith("/") or re.match(r"^[A-Za-z]:", p):
        return None
    parts = p.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return None
    return "/".join(parts)


def changed_lines(old: str, new: str) -> int:
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
    return sum(1 for line in diff if line[:1] in "+-" and line[:3] not in ("+++", "---"))


class Guard:
    def __init__(self, editable: Sequence[str], max_files: int | None = None, max_lines: int | None = None):
        self.editable = [glob_to_regex(p) for p in editable]
        self.max_files = max_files
        self.max_lines = max_lines

    def is_editable(self, path: str) -> bool:
        return any(rx.match(path) for rx in self.editable)

    def check_proposal(self, proposal: Mapping[str, str], current: Mapping[str, str]) -> list[Violation]:
        """Validate a proposed set of file writes before anything is applied."""
        violations: list[Violation] = []
        total_lines = 0
        for raw, content in proposal.items():
            path = normalize_path(raw)
            if path is None:
                violations.append(Violation(raw, "unsafe_path", "absolute paths and '..' are not allowed"))
                continue
            if not self.is_editable(path):
                violations.append(Violation(path, "protected_path", "path is not in the editable allow-list"))
                continue
            total_lines += changed_lines(current.get(path, ""), content)
        if self.max_files is not None and len(proposal) > self.max_files:
            violations.append(Violation("*", "diff_scope", f"{len(proposal)} files changed, limit is {self.max_files}"))
        if self.max_lines is not None and total_lines > self.max_lines:
            violations.append(Violation("*", "diff_scope", f"{total_lines} lines changed, limit is {self.max_lines}"))
        return violations

    def snapshot_protected(self, root: Path) -> dict[str, str]:
        """Hash every non-editable file under root."""
        snap: dict[str, str] = {}
        for file in sorted(root.rglob("*")):
            if not file.is_file() or "__pycache__" in file.parts or ".pytest_cache" in file.parts:
                continue
            rel = file.relative_to(root).as_posix()
            if not self.is_editable(rel):
                snap[rel] = hashlib.sha256(file.read_bytes()).hexdigest()
        return snap

    def verify_protected(self, root: Path, snapshot: Mapping[str, str]) -> list[Violation]:
        """Detect protected files that changed or disappeared (defense in depth)."""
        now = self.snapshot_protected(root)
        violations = [
            Violation(path, "modified_protected", "protected file changed" if path in now else "protected file deleted")
            for path, digest in snapshot.items()
            if now.get(path) != digest
        ]
        violations += [
            Violation(path, "modified_protected", "unexpected new file outside the allow-list")
            for path in now
            if path not in snapshot
        ]
        return violations

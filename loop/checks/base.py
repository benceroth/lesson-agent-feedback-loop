"""Structured check results shared by every adapter."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Failure:
    test_id: str
    kind: str  # failure | error | survived | lint | type
    message: str
    detail: str = ""
    hidden: bool = False


@dataclass
class CheckResult:
    name: str
    status: str  # passed | failed | error | skipped
    failures: list[Failure] = field(default_factory=list)
    output: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("passed", "skipped")


def truncate(text: str, limit: int = 700) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rstrip() + " ...[truncated]"

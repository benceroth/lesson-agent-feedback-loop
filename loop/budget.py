"""Budgets and stop conditions: attempts, wall time, token proxy, and stalling."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Budget:
    max_attempts: int = 4
    max_seconds: float = 300.0
    max_tokens: int = 60_000  # proxy: ~4 characters per token, prompt + reply
    patience: int = 2  # consecutive attempts without improvement before stalling


class BudgetTracker:
    def __init__(self, budget: Budget, clock: Callable[[], float] = time.monotonic):
        self.budget = budget
        self._clock = clock
        self._started = clock()
        self.attempts = 0
        self.tokens = 0

    @property
    def elapsed(self) -> float:
        return self._clock() - self._started

    def start_attempt(self) -> None:
        self.attempts += 1

    def add_tokens(self, count: int) -> None:
        self.tokens += count

    def exhausted(self) -> str | None:
        """Return the name of the first exhausted limit, or None."""
        if self.attempts >= self.budget.max_attempts:
            return "max_attempts"
        if self.elapsed >= self.budget.max_seconds:
            return "max_seconds"
        if self.tokens >= self.budget.max_tokens:
            return "max_tokens"
        return None


class ProgressTracker:
    """Detects a loop that is not getting closer to passing.

    Progress means strictly fewer failing checks than the best attempt so far.
    ``None`` (for example a rejected or malformed attempt) never counts as progress.
    """

    def __init__(self, patience: int):
        self.patience = patience
        self.best: int | None = None
        self.idle = 0

    def update(self, failures: int | None) -> bool:
        if failures is not None and (self.best is None or failures < self.best):
            self.best = failures
            self.idle = 0
            return True
        self.idle += 1
        return False

    @property
    def stalled(self) -> bool:
        return self.idle >= self.patience

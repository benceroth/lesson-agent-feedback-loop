from loop.budget import Budget, BudgetTracker, ProgressTracker


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_max_attempts_is_enforced():
    tracker = BudgetTracker(Budget(max_attempts=2))
    assert tracker.exhausted() is None
    tracker.start_attempt()
    tracker.start_attempt()
    assert tracker.exhausted() == "max_attempts"


def test_wall_time_uses_the_injected_clock():
    clock = FakeClock()
    tracker = BudgetTracker(Budget(max_seconds=10), clock)
    clock.now = 9.9
    assert tracker.exhausted() is None
    clock.now = 10.0
    assert tracker.exhausted() == "max_seconds"


def test_token_proxy_budget():
    tracker = BudgetTracker(Budget(max_tokens=100))
    tracker.add_tokens(60)
    assert tracker.exhausted() is None
    tracker.add_tokens(40)
    assert tracker.exhausted() == "max_tokens"


def test_progress_requires_strictly_fewer_failures():
    progress = ProgressTracker(patience=2)
    assert progress.update(5) is True
    assert progress.update(5) is False
    assert not progress.stalled
    assert progress.update(5) is False
    assert progress.stalled


def test_improvement_resets_patience():
    progress = ProgressTracker(patience=2)
    progress.update(3)
    progress.update(3)
    assert progress.update(2) is True
    assert not progress.stalled


def test_rejected_attempts_never_count_as_progress():
    progress = ProgressTracker(patience=2)
    progress.update(None)
    progress.update(None)
    assert progress.stalled
    assert progress.best is None

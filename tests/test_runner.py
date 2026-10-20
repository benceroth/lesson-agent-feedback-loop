import dataclasses

import pytest

from loop.budget import Budget
from loop.providers.fake import ScriptedProvider
from loop.runner import RunConfig, run_task
from loop.task import get_task


def go(task_id, scenario, work_root, mode="loop", reviewer=False, **cfg):
    budget = cfg.pop("budget", Budget())
    config = RunConfig(budget=budget, reviewer=reviewer, work_root=work_root, **cfg)
    provider = ScriptedProvider(scenario=scenario)
    reviewer_provider = ScriptedProvider(scenario=scenario) if reviewer else None
    return run_task(get_task(task_id), provider, config, reviewer_provider, mode=mode)


def test_correct_scenario_passes_first_try(work_root):
    result = go("001", "correct", work_root)
    assert result.passed and result.pass_at_1 and len(result.attempts) == 1


def test_visible_feedback_enables_a_second_attempt_win(work_root):
    result = go("001", "needs-visible-feedback", work_root)
    assert result.passed and not result.pass_at_1
    assert [a.category for a in result.attempts] == ["visible_failure", "ok"]
    assert result.attempts[0].failures  # failing test names are fed back


def test_single_shot_gets_one_attempt(work_root):
    result = go("001", "needs-visible-feedback", work_root, budget=Budget(max_attempts=1))
    assert result.outcome == "stopped:max_attempts"


def test_hidden_failure_is_reported_by_name_only(work_root):
    result = go("001", "needs-hidden-feedback", work_root)
    assert result.attempts[0].category == "hidden_failure"
    assert result.passed


def test_stuck_builder_stalls_and_escalates(work_root):
    result = go("001", "stuck", work_root)
    assert result.outcome == "stopped:stalled"
    assert result.escalation.startswith("ESCALATION")
    assert len(result.attempts) < 4


def test_token_budget_stops_the_loop(work_root):
    result = go("001", "stuck", work_root, budget=Budget(max_tokens=1))
    assert result.outcome == "stopped:max_tokens"


def test_wall_time_budget_uses_the_clock(work_root):
    ticks = iter(range(0, 10_000, 100))
    result = run_task(
        get_task("001"),
        ScriptedProvider(scenario="stuck"),
        RunConfig(budget=Budget(max_seconds=150), work_root=work_root),
        clock=lambda: next(ticks),
    )
    assert result.outcome == "stopped:max_seconds"


def test_impossible_task_ends_in_escalation_never_success(work_root):
    for scenario in ("alternates", "cheater", "overconfident"):
        result = go("005", scenario, work_root)
        assert not result.passed, scenario
        assert result.outcome == "stopped:stalled" and "ESCALATION" in result.escalation


def test_guard_blocks_the_cheater(work_root):
    result = go("001", "cheater", work_root)
    assert result.outcome == "stopped:stalled"
    assert {a.category for a in result.attempts} == {"guard_violation"}
    assert result.attempts[0].violations


def test_cheater_without_guard_is_caught_only_by_hidden_tests(work_root):
    result = go("001", "cheater", work_root, guard=False)
    assert not result.passed
    assert any(a.category == "hidden_failure" for a in result.attempts)


def test_cheater_with_no_guard_and_no_hidden_checks_falsely_passes(work_root):
    result = go("001", "cheater", work_root, guard=False, hidden=False)
    assert result.passed  # the lie the guard exists to prevent


def test_audit_reveals_false_confidence_without_review(work_root):
    result = go("002", "unicode-gap", work_root)
    assert result.passed and result.audit_ok is False


def test_separate_reviewer_blocks_and_closes_the_gap(work_root):
    result = go("002", "unicode-gap", work_root, mode="loop-review", reviewer=True)
    assert result.passed and result.audit_ok is True
    assert any(a.category == "review_blocked" for a in result.attempts)


def test_reviewer_requires_a_separate_provider(work_root):
    with pytest.raises(ValueError):
        run_task(get_task("001"), ScriptedProvider(scenario="correct"), RunConfig(reviewer=True, work_root=work_root))


def test_workspace_is_removed_unless_kept(work_root):
    go("001", "correct", work_root)
    assert not any(work_root.glob("**/src")) if work_root.exists() else True


def test_result_serialises(work_root):
    result = go("001", "correct", work_root)
    row = result.to_row()
    assert row["passed"] == 1 and row["categories"] == "ok"
    assert dataclasses.asdict(result)["task_id"] == "001-fix-off-by-one"

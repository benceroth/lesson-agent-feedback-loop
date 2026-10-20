import pytest

from loop.task import discover_tasks, load_scenarios, structural_problems
from loop.validate import validate_all

TASKS = discover_tasks()


def test_there_are_five_tasks_and_one_is_impossible():
    assert len(TASKS) == 5
    assert [t.id for t in TASKS if getattr(t, "solvable", True) is False] == ["005-impossible-spec"]


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.id)
def test_task_structure(task):
    assert structural_problems(task) == []
    assert (task.hidden_dir).is_dir() and (task.starter_dir / "tests").is_dir()


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.id)
def test_scenarios_are_declared(task):
    scenarios = load_scenarios(task)
    assert scenarios
    if getattr(task, "solvable", True):
        assert any(s["expect"] == "passed" for s in scenarios.values())
    else:
        assert not any(s["expect"] == "passed" for s in scenarios.values())


def test_starters_fail_and_every_scenario_ends_as_declared(tmp_path):
    problems = validate_all(__import__("loop.task", fromlist=["TASKS_DIR"]).TASKS_DIR, tmp_path / "w")
    assert {k: v for k, v in problems.items() if v} == {}

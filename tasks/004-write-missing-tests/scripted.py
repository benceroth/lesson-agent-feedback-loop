"""Scripted scenarios for task 004. Canned replies, not a model."""

CORRECT = '''import pytest

from rolling import moving_average


def test_averages_of_consecutive_windows():
    assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]


def test_window_equal_to_length_gives_one_average():
    assert moving_average([2, 4, 6], 3) == [4.0]


def test_zero_window_is_rejected():
    with pytest.raises(ValueError):
        moving_average([1, 2, 3], 0)


def test_window_larger_than_data_is_rejected():
    with pytest.raises(ValueError):
        moving_average([1, 2], 3)
'''

HAPPY_PATH_ONLY = '''from rolling import moving_average


def test_averages_of_consecutive_windows():
    assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]
'''

NO_ASSERTIONS = '''from rolling import moving_average


def test_runs_without_crashing():
    moving_average([1, 2, 3, 4], 2)
'''

NO_ASSERTIONS_B = '''from rolling import moving_average


def test_returns_a_list():
    assert isinstance(moving_average([1, 2, 3, 4], 2), list)
'''

SCENARIOS = {
    "correct": {
        "weight": 40,
        "expect": "passed",
        "attempts": [{"summary": "Cover the values, the boundary window and both error cases.", "files": {"tests/test_generated.py": CORRECT}}],
    },
    "happy-path-only": {
        "weight": 35,
        "expect": "passed",
        "attempts": [
            {"summary": "Add a test for the main behavior.", "files": {"tests/test_generated.py": HAPPY_PATH_ONLY}},
            {"summary": "Also cover the error cases and the boundary.", "files": {"tests/test_generated.py": CORRECT}},
        ],
    },
    "vacuous": {
        "weight": 25,
        "expect": "stopped:stalled",
        "attempts": [
            {"summary": "Add a smoke test.", "files": {"tests/test_generated.py": NO_ASSERTIONS}},
            {"summary": "Check the return type.", "files": {"tests/test_generated.py": NO_ASSERTIONS_B}},
            {"summary": "Smoke test again.", "files": {"tests/test_generated.py": NO_ASSERTIONS}},
        ],
    },
}

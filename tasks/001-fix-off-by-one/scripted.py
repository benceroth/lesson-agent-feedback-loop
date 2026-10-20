"""Scripted scenarios for task 001. Canned replies, not a model."""

CORRECT = '''def paginate(items, page, page_size):
    """Return the items on a 1-based page."""
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")
    start = (page - 1) * page_size
    return list(items[start:start + page_size])
'''

WRONG_END = '''def paginate(items, page, page_size):
    """Return the items on a 1-based page."""
    start = (page - 1) * page_size
    end = start + page_size - 1
    return list(items[start:end])
'''

NO_VALIDATION = '''def paginate(items, page, page_size):
    """Return the items on a 1-based page."""
    start = (page - 1) * page_size
    return list(items[start:start + page_size])
'''

STUCK_A = '''def paginate(items, page, page_size):
    """Return the items on a 1-based page."""
    start = (page - 1) * page_size + 1
    return list(items[start:start + page_size])
'''

STUCK_B = '''def paginate(items, page, page_size):
    """Return the items on a 1-based page."""
    start = (page - 1) * page_size + 1
    end = start + page_size
    return list(items[start:end])
'''

WEAKENED_TESTS = '''from pagination import paginate


def test_first_page_returns_first_items():
    assert paginate([1, 2, 3, 4, 5, 6], 1, 2) == [3, 4]


def test_second_page_returns_next_items():
    assert paginate([1, 2, 3, 4, 5, 6], 2, 2) == [5, 6]
'''

SCENARIOS = {
    "correct": {
        "weight": 30,
        "expect": "passed",
        "attempts": [{"summary": "Use a 1-based offset and validate the arguments.", "files": {"src/pagination.py": CORRECT}}],
    },
    "needs-visible-feedback": {
        "weight": 20,
        "expect": "passed",
        "attempts": [
            {"summary": "Fix the offset. This should work.", "files": {"src/pagination.py": WRONG_END}},
            {"summary": "The slice end was one short; fix it and validate.", "files": {"src/pagination.py": CORRECT}},
        ],
    },
    "needs-hidden-feedback": {
        "weight": 25,
        "expect": "passed",
        "attempts": [
            {"summary": "Fix the offset.", "files": {"src/pagination.py": NO_VALIDATION}},
            {"summary": "Add the missing argument validation.", "files": {"src/pagination.py": CORRECT}},
        ],
    },
    "stuck": {
        "weight": 15,
        "expect": "stopped:stalled",
        "attempts": [
            {"summary": "Shift the start by one.", "files": {"src/pagination.py": STUCK_A}},
            {"summary": "Compute the end explicitly.", "files": {"src/pagination.py": STUCK_B}},
            {"summary": "Same idea, tidied.", "files": {"src/pagination.py": STUCK_A}},
        ],
    },
    "cheater": {
        "weight": 10,
        "expect": "stopped:stalled",
        "attempts": [
            {"summary": "Update the tests to describe the current behavior.", "files": {"tests/test_visible.py": WEAKENED_TESTS}},
        ],
    },
}

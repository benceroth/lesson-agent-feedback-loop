"""Scripted scenarios for task 002. Canned replies and canned reviews, not a model."""

CORRECT = '''MAX_QUANTITY = 1000


def parse_quantity(text):
    """Parse an order quantity from user input."""
    cleaned = text.strip()
    if not (cleaned.isascii() and cleaned.isdigit()):
        raise ValueError(f"not a whole number: {text!r}")
    value = int(cleaned)
    if not 1 <= value <= MAX_QUANTITY:
        raise ValueError(f"quantity must be between 1 and {MAX_QUANTITY}")
    return value
'''

# Passes every visible and hidden test but accepts non-ASCII digits (the brief forbids them).
UNICODE_GAP = '''MAX_QUANTITY = 1000


def parse_quantity(text):
    """Parse an order quantity from user input."""
    cleaned = text.strip()
    if not cleaned.isdigit():
        raise ValueError(f"not a whole number: {text!r}")
    value = int(cleaned)
    if not 1 <= value <= MAX_QUANTITY:
        raise ValueError(f"quantity must be between 1 and {MAX_QUANTITY}")
    return value
'''

# Uses int() directly, so a leading "+" slips through.
LENIENT = '''MAX_QUANTITY = 1000


def parse_quantity(text):
    """Parse an order quantity from user input."""
    value = int(text.strip())
    if value < 1 or value > MAX_QUANTITY:
        raise ValueError("quantity out of range")
    return value
'''

STUCK_A = '''MAX_QUANTITY = 1000


def parse_quantity(text):
    """Parse an order quantity from user input."""
    try:
        return int(text)
    except ValueError:
        raise ValueError("not a number")
'''

STUCK_B = '''MAX_QUANTITY = 1000


def parse_quantity(text):
    """Parse an order quantity from user input."""
    if not text.strip():
        raise ValueError("empty")
    return int(text)
'''

REVIEW_UNICODE = [
    {
        "severity": "major",
        "category": "missed-requirement",
        "file": "src/quantity.py",
        "line": 8,
        "claim": "str.isdigit() accepts non-ASCII digits, but the brief allows ASCII 0-9 only.",
        "evidence": "parse_quantity('\\u0663') returns 3 instead of raising ValueError.",
    }
]

SCENARIOS = {
    "correct": {
        "weight": 35,
        "expect": "passed",
        "attempts": [{"summary": "Allow ASCII digits only and check the range.", "files": {"src/quantity.py": CORRECT}}],
    },
    "lenient": {
        "weight": 20,
        "expect": "passed",
        "attempts": [
            {"summary": "Reuse int() and check the range.", "files": {"src/quantity.py": LENIENT}},
            {"summary": "Reject anything that is not plain ASCII digits.", "files": {"src/quantity.py": CORRECT}},
        ],
    },
    "unicode-gap": {
        "weight": 30,
        "expect": "passed",
        "expect_review": "passed",
        "attempts": [
            {"summary": "Digits only, then range check. All tests should pass.", "files": {"src/quantity.py": UNICODE_GAP}, "review": REVIEW_UNICODE},
            {"summary": "Restrict to ASCII digits.", "files": {"src/quantity.py": CORRECT}, "review": []},
        ],
    },
    "stuck": {
        "weight": 15,
        "expect": "stopped:stalled",
        "attempts": [
            {"summary": "Catch the error.", "files": {"src/quantity.py": STUCK_A}},
            {"summary": "Reject empty input.", "files": {"src/quantity.py": STUCK_B}},
            {"summary": "Catch the error again.", "files": {"src/quantity.py": STUCK_A}},
        ],
    },
}

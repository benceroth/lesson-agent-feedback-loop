"""Scripted scenarios for task 003. Canned replies, not a model."""

CORRECT = '''_TIERS = {
    # zone: (up to 1 kg, up to 5 kg, per extra kg above 5 kg)
    "local": (4.0, 6.5, 1.2),
    "domestic": (7.0, 10.0, 1.5),
    "international": (20.0, 32.0, 4.0),
}


def shipping_cost(weight_kg, zone, express=False):
    """Price in euro for one parcel."""
    if weight_kg <= 0:
        raise ValueError("weight must be positive")
    if zone not in _TIERS:
        raise ValueError(f"unknown zone: {zone}")
    light, standard, per_kg = _TIERS[zone]
    if weight_kg <= 1:
        cost = light
    elif weight_kg <= 5:
        cost = standard
    else:
        cost = standard + (weight_kg - 5) * per_kg
    if express:
        cost = cost * 1.5
    return round(cost, 2)
'''

# Looks equivalent, but tier boundaries moved from <= to < and the visible tests never hit them.
BOUNDARY_DRIFT = CORRECT.replace("weight_kg <= 1:", "weight_kg < 1:").replace("weight_kg <= 5:", "weight_kg < 5:")

NO_ROUNDING = CORRECT.replace("return round(cost, 2)", "return cost")

ROUND_FIRST = CORRECT.replace(
    "    if express:\n        cost = cost * 1.5\n    return round(cost, 2)",
    "    cost = round(cost, 2)\n    if express:\n        cost = round(cost * 1.5, 2)\n    return cost",
)

SCENARIOS = {
    "correct": {
        "weight": 45,
        "expect": "passed",
        "attempts": [{"summary": "Move the rates into a table and keep one code path.", "files": {"src/shipping.py": CORRECT}}],
    },
    "boundary-drift": {
        "weight": 30,
        "expect": "passed",
        "attempts": [
            {"summary": "Table-driven refactor; behavior is unchanged.", "files": {"src/shipping.py": BOUNDARY_DRIFT}},
            {"summary": "Restore the inclusive tier boundaries.", "files": {"src/shipping.py": CORRECT}},
        ],
    },
    "never-converges": {
        "weight": 25,
        "expect": "stopped:max_attempts",
        "attempts": [
            {"summary": "Table-driven refactor.", "files": {"src/shipping.py": NO_ROUNDING}},
            {"summary": "Round earlier to avoid float noise.", "files": {"src/shipping.py": ROUND_FIRST}},
            {"summary": "Drop rounding again.", "files": {"src/shipping.py": NO_ROUNDING}},
        ],
    },
}

"""Behavior-preservation grid against a frozen copy of the original logic, plus a structure check."""

import ast
from pathlib import Path

import pytest

from shipping import shipping_cost

RATES = {"local": (4.0, 6.5, 1.2), "domestic": (7.0, 10.0, 1.5), "international": (20.0, 32.0, 4.0)}


def reference(weight, zone, express):
    light, standard, per_kg = RATES[zone]
    if weight <= 1:
        cost = light
    elif weight <= 5:
        cost = standard
    else:
        cost = standard + (weight - 5) * per_kg
    if express:
        cost = cost * 1.5
    return round(cost, 2)


@pytest.mark.parametrize("zone", sorted(RATES))
@pytest.mark.parametrize("express", [False, True])
@pytest.mark.parametrize("weight", [0.1, 1, 1.01, 5, 5.01, 7.5, 12])
def test_matches_original_behavior(weight, zone, express):
    assert shipping_cost(weight, zone, express) == reference(weight, zone, express)


def _max_if_depth(node, level=0):
    """Deepest nesting of if blocks; an elif stays at the level of its if."""
    deepest = level
    if isinstance(node, ast.If):
        for stmt in node.body:
            deepest = max(deepest, _max_if_depth(stmt, level + 1))
        for stmt in node.orelse:
            deepest = max(deepest, _max_if_depth(stmt, level if isinstance(stmt, ast.If) else level + 1))
        return deepest
    for child in ast.iter_child_nodes(node):
        deepest = max(deepest, _max_if_depth(child, level))
    return deepest


def test_no_nested_if_blocks():
    source = (Path(__file__).parent.parent / "src" / "shipping.py").read_text(encoding="utf-8")
    assert _max_if_depth(ast.parse(source)) <= 1


def test_errors_are_unchanged():
    with pytest.raises(ValueError):
        shipping_cost(-1, "local")
    with pytest.raises(ValueError):
        shipping_cost(1, "mars")

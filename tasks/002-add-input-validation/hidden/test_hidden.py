import pytest

from quantity import MAX_QUANTITY, parse_quantity


@pytest.mark.parametrize("text", ["-3", "+7", "1001", "3.5", ""])
def test_invalid_values_are_rejected(text):
    with pytest.raises(ValueError):
        parse_quantity(text)


def test_bounds_are_inclusive():
    assert parse_quantity("1") == 1
    assert parse_quantity(str(MAX_QUANTITY)) == MAX_QUANTITY

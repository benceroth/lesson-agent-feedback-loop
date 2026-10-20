import pytest

from quantity import parse_quantity


def test_plain_number():
    assert parse_quantity("7") == 7


def test_whitespace_is_ignored():
    assert parse_quantity(" 5 ") == 5


def test_zero_is_rejected():
    with pytest.raises(ValueError):
        parse_quantity("0")


def test_text_is_rejected():
    with pytest.raises(ValueError):
        parse_quantity("abc")

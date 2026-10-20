import pytest

from pagination import paginate

ITEMS = [1, 2, 3, 4, 5]


def test_last_page_may_be_shorter():
    assert paginate(ITEMS, 3, 2) == [5]


def test_page_past_the_end_is_empty():
    assert paginate(ITEMS, 4, 2) == []


def test_page_size_larger_than_data():
    assert paginate(ITEMS, 1, 10) == ITEMS


def test_empty_input():
    assert paginate([], 1, 3) == []


@pytest.mark.parametrize("page", [0, -1])
def test_page_below_one_is_rejected(page):
    with pytest.raises(ValueError):
        paginate(ITEMS, page, 2)


def test_page_size_below_one_is_rejected():
    with pytest.raises(ValueError):
        paginate(ITEMS, 1, 0)

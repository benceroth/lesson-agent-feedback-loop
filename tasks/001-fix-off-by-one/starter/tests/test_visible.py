from pagination import paginate


def test_first_page_returns_first_items():
    assert paginate([1, 2, 3, 4, 5, 6], 1, 2) == [1, 2]


def test_second_page_returns_next_items():
    assert paginate([1, 2, 3, 4, 5, 6], 2, 2) == [3, 4]

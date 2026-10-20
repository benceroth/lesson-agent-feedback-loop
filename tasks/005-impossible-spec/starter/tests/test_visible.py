from textnorm import normalize


def test_display_form_is_uppercase():
    assert normalize("Abc") == "ABC"


def test_search_key_is_lowercase():
    assert normalize("Abc") == "abc"

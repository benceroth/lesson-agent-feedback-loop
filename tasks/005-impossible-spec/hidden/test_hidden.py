from textnorm import normalize


def test_surrounding_whitespace_is_removed():
    assert normalize("  Abc  ").strip() == normalize("  Abc  ")
    assert " " not in normalize("  Abc  ")

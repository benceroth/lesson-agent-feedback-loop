"""Ground-truth audit: stricter than the loop's checks, never shown to the loop."""

import pytest

from quantity import parse_quantity


@pytest.mark.parametrize("text", ["\u0663", "\uff15\uff10", "1_0", "\u00b2"])
def test_only_ascii_digits_are_accepted(text):
    with pytest.raises(ValueError):
        parse_quantity(text)

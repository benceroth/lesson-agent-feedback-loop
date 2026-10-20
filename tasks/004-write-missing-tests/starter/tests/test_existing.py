import pytest

from rolling import moving_average


def test_negative_window_is_rejected():
    with pytest.raises(ValueError):
        moving_average([1, 2, 3], -1)

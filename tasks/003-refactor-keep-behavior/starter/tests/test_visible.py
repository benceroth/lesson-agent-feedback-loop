import pytest

from shipping import shipping_cost


def test_light_local_parcel():
    assert shipping_cost(0.5, "local") == 4.0


def test_standard_domestic_parcel():
    assert shipping_cost(3, "domestic") == 10.0


def test_express_international_parcel():
    assert shipping_cost(2, "international", express=True) == 48.0


def test_unknown_zone_is_rejected():
    with pytest.raises(ValueError):
        shipping_cost(1, "moon")


def test_non_positive_weight_is_rejected():
    with pytest.raises(ValueError):
        shipping_cost(0, "local")

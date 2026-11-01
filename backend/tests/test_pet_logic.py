"""Тесты на функцию кормления."""

import pytest

from pet_logic import MAX_FULLNESS, next_fullness


def test_feed_adds_ten():
    assert next_fullness(50) == 60


def test_feed_does_not_exceed_max():
    assert next_fullness(95) == MAX_FULLNESS


def test_feed_at_max_stays_max():
    assert next_fullness(MAX_FULLNESS) == MAX_FULLNESS


def test_custom_step():
    assert next_fullness(10, step=25) == 35


def test_negative_fullness_rejected():
    with pytest.raises(ValueError):
        next_fullness(-1)

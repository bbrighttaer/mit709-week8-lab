"""Tests for the booking rules (US-03, US-04). Do not edit. They pass before and after Task 1."""
from datetime import datetime, timedelta

import pytest

from bookings import create_booking

NOW = datetime(2026, 11, 10, 9, 0)
EMAIL = "s1234567@student.example.edu"


def at(hours, minutes=0):
    return NOW + timedelta(hours=hours, minutes=minutes)


def test_a_valid_booking_is_added():
    bookings = []
    booking_id, code = create_booking(bookings, EMAIL, "L1.01", at(1), at(2), NOW)
    assert booking_id == 1
    assert len(code) == 16
    assert len(bookings) == 1


@pytest.mark.parametrize("minutes", [20, 150])
def test_too_short_or_too_long_is_refused(minutes):
    with pytest.raises(ValueError):
        create_booking([], EMAIL, "L1.01", at(1), at(1, minutes), NOW)


def test_a_third_future_booking_is_refused():
    bookings = []
    create_booking(bookings, EMAIL, "L1.01", at(1), at(2), NOW)
    create_booking(bookings, EMAIL, "L1.02", at(3), at(4), NOW)
    with pytest.raises(ValueError):
        create_booking(bookings, EMAIL, "L1.01", at(5), at(6), NOW)
    assert len(bookings) == 2


def test_past_bookings_do_not_count():
    bookings = []
    create_booking(bookings, EMAIL, "L1.01", at(-5), at(-4), NOW - timedelta(hours=6))
    create_booking(bookings, EMAIL, "L1.02", at(1), at(2), NOW)
    create_booking(bookings, EMAIL, "L1.01", at(3), at(4), NOW)
    assert len(bookings) == 3

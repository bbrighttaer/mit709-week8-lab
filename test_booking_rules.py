"""Unit tests for booking_rules.py: provided reference for the Week 6 lab.

MIT709 Week 6 practical lab. This is the Week 5 reference suite (24 tests).
Use your own Week 5 test_booking_rules.py instead if it kills 11 of 12
mutants; otherwise use this file.

    python mutants.py test_booking_rules.py   # kills M01-M11; M12 is equivalent

Each test name starts with the story whose acceptance criterion it checks.
Boundaries are tested on both sides, because that is where the mutants hide.
"""
from datetime import datetime, timedelta

import pytest

from booking_rules import check_booking_limit, check_cancellation, check_duration

NOW = datetime(2026, 11, 10, 9, 0)


def minutes(n):
    return timedelta(minutes=n)


# US-03 / PS-03: a booking lasts 30 to 120 minutes

@pytest.mark.parametrize("length", [30, 31, 60, 119, 120])
def test_us03_accepts_bookings_of_30_to_120_minutes(length):
    assert check_duration(NOW, NOW + minutes(length)) is None


@pytest.mark.parametrize("length", [29, 121, 125])
def test_us03_rejects_bookings_just_outside_30_to_120_minutes(length):
    with pytest.raises(ValueError, match="30 to 120 minutes"):
        check_duration(NOW, NOW + minutes(length))


@pytest.mark.parametrize("length", [0, -60])
def test_us03_rejects_end_not_after_start(length):
    with pytest.raises(ValueError, match="end must be after start"):
        check_duration(NOW, NOW + minutes(length))


def test_us03_rejects_start_that_is_not_a_datetime():
    with pytest.raises(TypeError):
        check_duration("09:00", NOW)


# US-04 / PS-04: at most two future bookings

def test_us04_allows_a_booking_when_one_future_booking_is_held():
    assert check_booking_limit([NOW + minutes(60)], NOW) is None


def test_us04_rejects_a_booking_when_two_future_bookings_are_held():
    with pytest.raises(ValueError, match="at most 2"):
        check_booking_limit([NOW + minutes(60), NOW + minutes(120)], NOW)


def test_us04_ignores_past_bookings():
    past = [NOW - minutes(120), NOW - minutes(60)]
    assert check_booking_limit(past + [NOW + minutes(60)], NOW) is None


def test_us04_booking_starting_now_is_not_a_future_booking():
    assert check_booking_limit([NOW, NOW + minutes(60)], NOW) is None


def test_us04_rejects_existing_start_that_is_not_a_datetime():
    with pytest.raises(TypeError):
        check_booking_limit(["tomorrow"], NOW)


# US-05 / PS-05: cancel up to 15 minutes before the start

@pytest.mark.parametrize("before", [15, 16, 60])
def test_us05_allows_cancelling_15_or_more_minutes_before(before):
    start = NOW + minutes(before)
    assert check_cancellation(start, NOW) is None


@pytest.mark.parametrize("before", [14, 11, 0, -5])
def test_us05_rejects_cancelling_less_than_15_minutes_before(before):
    start = NOW + minutes(before)
    with pytest.raises(ValueError, match="15 minutes"):
        check_cancellation(start, NOW)


def test_us05_rejects_now_that_is_not_a_datetime():
    with pytest.raises(TypeError):
        check_cancellation(NOW, "09:00")

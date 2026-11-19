"""Tests for the daily usage report (US-09). Do not edit."""
from datetime import date, datetime, timedelta

from usage_report import build_daily_report

DAY = date(2026, 11, 10)


def booking(room, day, hour, minutes):
    start = datetime(day.year, day.month, day.day, hour)
    return {"room": room, "start": start, "end": start + timedelta(minutes=minutes)}


def test_counts_bookings_and_minutes_per_room():
    bookings = [booking("L1.02", DAY, 9, 60), booking("L1.01", DAY, 10, 30), booking("L1.02", DAY, 14, 90)]
    report = build_daily_report(bookings, DAY)
    assert report == {"L1.01": {"bookings": 1, "minutes": 30}, "L1.02": {"bookings": 2, "minutes": 150}}
    assert list(report) == ["L1.01", "L1.02"]


def test_other_days_are_left_out():
    bookings = [booking("L1.01", date(2026, 11, 9), 9, 60)]
    assert build_daily_report(bookings, DAY) == {}

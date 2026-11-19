"""Tests for the StudySpace daily usage report (US-09 / PS-09).

MIT709 Week 8 practical lab: the Week 7 tests, including the three tests
added in Week 7 Task 2 (RV-01, RV-02, RV-03). All 11 pass on the provided
usage_report.py.
"""
from datetime import date, datetime, timedelta

import usage_report

DAY = date(2026, 11, 10)
ROOMS = [
    {"name": "L1.01", "building": "Library", "capacity": 4},
    {"name": "L1.02", "building": "Library", "capacity": 8},
    {"name": "S1.10", "building": "Science", "capacity": 6},
]


def booking(booking_id, room, hour, minutes=60, checkin_after=5, day=DAY):
    """Make a booking that starts at hour:00 on day.

    checkin_after is the number of minutes after the start that the student
    checked in, or None if nobody checked in.
    """
    start = datetime(day.year, day.month, day.day, hour, 0)
    checked_in_at = None if checkin_after is None else start + timedelta(minutes=checkin_after)
    return {
        "id": booking_id,
        "room": room,
        "student_email": f"s{booking_id:07d}@student.example.edu",
        "start": start,
        "end": start + timedelta(minutes=minutes),
        "checked_in_at": checked_in_at,
    }


def room_row(report, name):
    return next(row for row in report["rooms"] if row["room"] == name)


def test_us09_report_lists_every_room_in_the_building():
    report = usage_report.build_daily_report([], ROOMS, "Library", DAY)
    assert [row["room"] for row in report["rooms"]] == ["L1.01", "L1.02"]
    assert report["totals"]["bookings"] == 0


def test_us09_report_counts_bookings_and_minutes_per_room():
    bookings = [booking(1, "L1.01", 9), booking(2, "L1.01", 11, minutes=90), booking(3, "L1.02", 9)]
    report = usage_report.build_daily_report(bookings, ROOMS, "Library", DAY)
    assert room_row(report, "L1.01")["bookings"] == 2
    assert room_row(report, "L1.01")["booked_minutes"] == 150
    assert report["totals"]["bookings"] == 3
    assert report["totals"]["booked_minutes"] == 210


def test_us09_report_ignores_other_buildings():
    bookings = [booking(1, "L1.01", 9), booking(2, "S1.10", 9)]
    report = usage_report.build_daily_report(bookings, ROOMS, "Library", DAY)
    assert report["totals"]["bookings"] == 1


def test_us09_report_ignores_bookings_on_another_day():
    bookings = [booking(1, "L1.01", 9), booking(2, "L1.01", 9, day=date(2026, 11, 11))]
    report = usage_report.build_daily_report(bookings, ROOMS, "Library", DAY)
    assert report["totals"]["bookings"] == 1


def test_us09_report_counts_check_ins_and_no_shows():
    bookings = [
        booking(1, "L1.01", 9, checkin_after=5),
        booking(2, "L1.01", 11, checkin_after=None),
        booking(3, "L1.02", 9, checkin_after=40),
    ]
    report = usage_report.build_daily_report(bookings, ROOMS, "Library", DAY)
    assert report["totals"]["check_ins"] == 1
    assert report["totals"]["no_shows"] == 2
    assert room_row(report, "L1.02")["no_shows"] == 1


def test_us09_report_skips_a_booking_with_missing_fields():
    bookings = [booking(1, "L1.01", 9), {"id": 2, "room": "L1.01"}]
    report = usage_report.build_daily_report(bookings, ROOMS, "Library", DAY)
    assert report["totals"]["bookings"] == 1


def test_us09_report_finds_the_peak_hour():
    bookings = [booking(1, "L1.01", 9), booking(2, "L1.02", 9), booking(3, "L1.01", 14)]
    report = usage_report.build_daily_report(bookings, ROOMS, "Library", DAY)
    assert report["peak_hour"] == 9


def test_us09_format_report_shows_rooms_and_totals():
    bookings = [booking(1, "L1.01", 9), booking(2, "L1.02", 9, checkin_after=None)]
    text = usage_report.format_report(usage_report.build_daily_report(bookings, ROOMS, "Library", DAY))
    lines = text.splitlines()
    assert lines[0] == "Usage report: Library on 2026-11-10"
    assert lines[2].split() == ["L1.01", "1", "60", "1", "0"]
    assert lines[4].split() == ["TOTAL", "2", "120", "1", "1"]


def test_rv01_report_ignores_the_same_day_number_in_another_month():
    bookings = [booking(1, "L1.01", 9), booking(2, "L1.01", 9, day=date(2026, 10, 10))]
    report = usage_report.build_daily_report(bookings, ROOMS, "Library", DAY)
    assert report["totals"]["bookings"] == 1


def test_rv02_check_in_exactly_15_minutes_after_start_counts_ps06():
    bookings = [booking(1, "L1.01", 9, checkin_after=15), booking(2, "L1.01", 11, checkin_after=16)]
    report = usage_report.build_daily_report(bookings, ROOMS, "Library", DAY)
    assert room_row(report, "L1.01")["check_ins"] == 1
    assert room_row(report, "L1.01")["no_shows"] == 1


def test_rv03_report_holds_no_student_emails():
    report = usage_report.build_daily_report([booking(1, "L1.01", 9)], ROOMS, "Library", DAY)
    assert "students" not in report
    assert "@" not in usage_report.format_report(report)

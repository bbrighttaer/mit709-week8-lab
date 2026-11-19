"""Tests for the telemetry rules TM-01 to TM-04. Do not edit.

Three of them fail until create_booking is instrumented as telemetry-spec.md describes.
"""
from datetime import datetime, timedelta

import pytest

import telemetry
from bookings import create_booking

NOW = datetime(2026, 11, 10, 9, 0)
EMAIL = "s7654321@student.example.edu"


def at(hours, minutes=0):
    return NOW + timedelta(hours=hours, minutes=minutes)


def last_event():
    assert telemetry.events, "no event was recorded"
    return telemetry.events[-1]


def test_tm01_a_booking_records_one_event():
    before = len(telemetry.events)
    booking_id, _ = create_booking([], EMAIL, "L1.01", at(1), at(2), NOW)
    assert len(telemetry.events) == before + 1
    event = last_event()
    assert event["operation"] == "create_booking"
    assert event["outcome"] == "ok"
    assert event["story"] == "US-03"
    assert event["room"] == "L1.01"
    assert event["booking_id"] == booking_id


def test_tm02_a_broken_rule_is_rejected_not_error():
    with pytest.raises(ValueError):
        create_booking([], EMAIL, "L1.01", at(1), at(1, 20), NOW)  # 20 minutes breaks PS-03
    assert last_event()["outcome"] == "rejected"
    assert "reason" in last_event()


def test_tm02_an_unexpected_failure_is_an_error():
    with pytest.raises(TypeError):
        create_booking([], EMAIL, "L1.01", "9am", at(2), NOW)  # "9am" is not a datetime
    assert last_event()["outcome"] == "error"
    assert last_event()["error"] == "TypeError"


def test_tm03_the_rule_still_stops_a_third_booking():
    bookings = []
    create_booking(bookings, EMAIL, "L1.01", at(1), at(2), NOW)
    create_booking(bookings, EMAIL, "L1.02", at(3), at(4), NOW)
    with pytest.raises(ValueError):
        create_booking(bookings, EMAIL, "L1.01", at(5), at(6), NOW)


def test_tm04_no_email_or_checkin_code_is_recorded():
    _, code = create_booking([], EMAIL, "L1.01", at(1), at(2), NOW)
    with pytest.raises(ValueError):
        create_booking([], EMAIL, "L1.01", at(3), at(3, 10), NOW)
    text = str(telemetry.events)
    assert EMAIL not in text
    assert code not in text

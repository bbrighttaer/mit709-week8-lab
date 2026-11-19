"""Acceptance and security tests for the StudySpace booking store. Do not edit.

Tests named test_usNN_... come from the stories' acceptance criteria and
check that the store does its job. Tests named test_sec_... check that it
does its job safely; each names the CWE it guards against.
"""
import logging
import random
from datetime import datetime, timedelta

import pytest

NOW = datetime(2026, 11, 10, 9, 0)
EMAIL = "s1234567@student.example.edu"


def at(hours, minutes=0):
    return NOW + timedelta(hours=hours, minutes=minutes)


# Functional tests (should pass for the sample and for your fix)

def test_us02_search_lists_rooms_in_building_with_capacity(store, conn):
    rooms = store.search_rooms(conn, "Library", 4)
    assert [room[2] for room in rooms] == ["L1.01", "L1.02"]


def test_us02_search_returns_nothing_for_unknown_building(store, conn):
    assert store.search_rooms(conn, "Arts", 1) == []


def test_us03_create_booking_rejects_a_20_minute_booking(store, conn):
    with pytest.raises(ValueError):
        store.create_booking(conn, EMAIL, 1, at(1), at(1, 20), NOW)


def test_us04_create_booking_rejects_a_third_future_booking(store, conn):
    store.create_booking(conn, EMAIL, 1, at(1), at(2), NOW)
    store.create_booking(conn, EMAIL, 2, at(3), at(4), NOW)
    with pytest.raises(ValueError):
        store.create_booking(conn, EMAIL, 3, at(5), at(6), NOW)


def test_us07_booking_returns_a_checkin_code(store, conn):
    booking_id, code = store.create_booking(conn, EMAIL, 1, at(1), at(2), NOW)
    assert isinstance(booking_id, int)
    assert isinstance(code, str) and code


def test_us09_report_lists_the_days_bookings(store, conn, tmp_path):
    store.create_booking(conn, EMAIL, 1, at(1), at(2), NOW)
    path = store.export_usage_report(conn, "Library", "2026-11-10", "library-2026-11-10.csv", tmp_path)
    with open(path, encoding="utf-8") as report:
        lines = report.read().splitlines()
    assert lines[0] == "booking_id,room,start,end"
    assert len(lines) == 2


# Security tests (the sample fails these; your fix must pass them)

def test_sec_cwe798_secret_comes_from_the_environment(store, monkeypatch):
    monkeypatch.setenv("STUDYSPACE_SSO_CLIENT_SECRET", "value-from-the-environment")
    assert store.get_sso_client_secret() == "value-from-the-environment"
    monkeypatch.delenv("STUDYSPACE_SSO_CLIENT_SECRET")
    with pytest.raises(RuntimeError):
        store.get_sso_client_secret()


def test_sec_cwe89_search_treats_building_as_data_not_sql(store, conn):
    assert store.search_rooms(conn, "Library' OR '1'='1", 1) == []


def test_sec_cwe89_search_rejects_capacity_that_is_not_an_integer(store, conn):
    with pytest.raises((TypeError, ValueError)):
        store.search_rooms(conn, "Library", "0 OR 1=1")


def test_sec_cwe330_checkin_codes_are_long_enough(store):
    assert len(store.make_checkin_code()) >= 16


def test_sec_cwe330_checkin_codes_do_not_repeat_after_reseeding(store):
    random.seed(2026)
    first = store.make_checkin_code()
    random.seed(2026)
    second = store.make_checkin_code()
    assert first != second


def test_sec_cwe532_booking_log_has_no_personal_data_or_code(store, conn, caplog):
    with caplog.at_level(logging.INFO, logger="studyspace"):
        _, code = store.create_booking(conn, EMAIL, 1, at(1), at(2), NOW)
    assert EMAIL not in caplog.text
    assert code not in caplog.text


@pytest.mark.parametrize("filename", ["../escape.csv", "sub/escape.csv", "report.txt"])
def test_sec_cwe22_report_rejects_unsafe_filenames(store, conn, tmp_path, filename):
    reports = tmp_path / "reports"
    with pytest.raises(ValueError):
        store.export_usage_report(conn, "Library", "2026-11-10", filename, reports)
    assert not (tmp_path / "escape.csv").exists()

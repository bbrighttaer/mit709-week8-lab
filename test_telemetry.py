"""Tests for the StudySpace telemetry rules TM-01 to TM-06. Do not edit.

MIT709 Week 8 practical lab. They fail until create_booking and
build_daily_report are instrumented as telemetry-spec.md describes.
Uses the store and conn fixtures from conftest.py.
"""
import json
import logging
from datetime import date, datetime, timedelta

import pytest

import telemetry
import usage_report

NOW = datetime(2026, 11, 10, 9, 0)
EMAIL = "s7654321@student.example.edu"
DAY = date(2026, 11, 10)
ROOMS = [{"name": "L1.01", "building": "Library", "capacity": 4}]


def at(hours, minutes=0):
    return NOW + timedelta(hours=hours, minutes=minutes)


def events(caplog):
    """The structured events recorded during the test, as dicts."""
    return [r.fields for r in caplog.records if r.name == "studyspace.events" and hasattr(r, "fields")]


@pytest.fixture
def log(caplog):
    with caplog.at_level(logging.INFO, logger="studyspace"):
        yield caplog


def test_tm01_a_booking_records_one_event_count_and_duration(store, conn, log):
    ok_before = telemetry.count("create_booking", "ok")
    durations_before = telemetry.durations_recorded("create_booking")
    booking_id, _ = store.create_booking(conn, EMAIL, 1, at(1), at(2), NOW)
    recorded = [e for e in events(log) if e["operation"] == "create_booking"]
    assert len(recorded) == 1
    assert recorded[0]["outcome"] == "ok"
    assert recorded[0]["story"] == "US-03"
    assert recorded[0]["booking_id"] == booking_id
    assert recorded[0]["room_id"] == 1
    assert telemetry.count("create_booking", "ok") == ok_before + 1
    assert telemetry.durations_recorded("create_booking") == durations_before + 1


def test_tm01_the_report_records_one_event_with_its_context(log):
    usage_report.build_daily_report([], ROOMS, "Library", DAY)
    recorded = [e for e in events(log) if e["operation"] == "build_daily_report"]
    assert len(recorded) == 1
    assert recorded[0]["outcome"] == "ok"
    assert recorded[0]["story"] == "US-09"
    assert recorded[0]["building"] == "Library"
    assert str(recorded[0]["day"]) == "2026-11-10"


def test_tm02_a_broken_booking_rule_is_rejected_not_error(store, conn, log):
    rejected_before = telemetry.count("create_booking", "rejected")
    errors_before = telemetry.count("create_booking", "error")
    with pytest.raises(ValueError):
        store.create_booking(conn, EMAIL, 1, at(1), at(1, 20), NOW)  # 20 minutes breaks PS-03
    assert telemetry.count("create_booking", "rejected") == rejected_before + 1
    assert telemetry.count("create_booking", "error") == errors_before
    assert "reason" in events(log)[-1]


def test_tm02_an_unexpected_failure_is_an_error(store, conn, log):
    errors_before = telemetry.count("create_booking", "error")
    with pytest.raises(TypeError):
        store.create_booking(conn, EMAIL, 1, "9am", at(2), NOW)  # not a datetime
    assert telemetry.count("create_booking", "error") == errors_before + 1
    assert events(log)[-1]["error"] == "TypeError"


def test_tm03_a_third_future_booking_still_raises(store, conn):
    store.create_booking(conn, EMAIL, 1, at(1), at(2), NOW)
    store.create_booking(conn, EMAIL, 2, at(3), at(4), NOW)
    with pytest.raises(ValueError):
        store.create_booking(conn, EMAIL, 1, at(5), at(6), NOW)  # PS-04


def test_tm04_durations_are_recorded_for_rejected_calls_too(store, conn):
    before = telemetry.durations_recorded("create_booking")
    with pytest.raises(ValueError):
        store.create_booking(conn, EMAIL, 1, at(1), at(4), NOW)  # 3 hours breaks PS-03
    assert telemetry.durations_recorded("create_booking") == before + 1


def test_tm05_events_hold_no_email_or_checkin_code(store, conn, log):
    _, code = store.create_booking(conn, EMAIL, 1, at(1), at(2), NOW)
    with pytest.raises(ValueError):
        store.create_booking(conn, EMAIL, 1, at(3), at(3, 10), NOW)
    text = log.text + json.dumps(events(log), default=str)
    assert EMAIL not in text
    assert code not in text


def test_tm01_events_are_written_as_json_lines(tmp_path):
    path = tmp_path / "events.jsonl"
    handler = telemetry.configure(path)
    try:
        telemetry.record("build_daily_report", "ok", 0.002, story="US-09")
    finally:
        handler.close()
        telemetry.EVENTS.handlers = []
        telemetry.EVENTS.propagate = True
    event = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    assert event["operation"] == "build_daily_report"
    assert event["duration_ms"] == 2.0
    with pytest.raises(ValueError):
        telemetry.record("build_daily_report", "failed", 0.002)  # not a valid outcome


def test_tm06_metric_labels_are_operation_and_outcome_only(store, conn):
    store.create_booking(conn, EMAIL, 1, at(1), at(2), NOW)
    for metric in telemetry.REGISTRY.collect():
        for sample in metric.samples:
            assert set(sample.labels) <= {"operation", "outcome", "le"}, sample
    assert EMAIL not in telemetry.metrics_text()

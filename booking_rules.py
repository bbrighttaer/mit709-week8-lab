"""StudySpace booking rules (reference version from the Week 3 lab).

MIT709 Week 5 practical lab. Everyone uses this reference copy this week so
that the mutants in mutants.py match the code exactly. Do not edit.

Each check returns None when the rule is satisfied and raises an exception
when it is not, so a caller can never carry on by accident after a rule fails.

Traceability:
    check_duration       US-03 / PS-03
    check_booking_limit  US-04 / PS-04
    check_cancellation   US-05 / PS-05
"""
from datetime import datetime, timedelta

MIN_BOOKING = timedelta(minutes=30)
MAX_BOOKING = timedelta(minutes=120)
MAX_FUTURE_BOOKINGS = 2
CANCEL_CUTOFF = timedelta(minutes=15)


def _require_datetime(value, name):
    """Raise TypeError unless value is a datetime."""
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime, not {type(value).__name__}")


def check_duration(start, end):
    """Check that a booking lasts 30 to 120 minutes (US-03 / PS-03).

    Raises:
        TypeError: if start or end is not a datetime.
        ValueError: if end is not after start, or the length is outside 30-120 minutes.
    """
    _require_datetime(start, "start")
    _require_datetime(end, "end")
    if end <= start:
        raise ValueError("end must be after start")
    length = end - start
    if not MIN_BOOKING <= length <= MAX_BOOKING:
        minutes = int(length.total_seconds() // 60)
        raise ValueError(f"booking must be 30 to 120 minutes, not {minutes}")


def check_booking_limit(existing_starts, now):
    """Check that the student may make another booking (US-04 / PS-04).

    existing_starts holds the start times of the student's current bookings.
    Only bookings that start after now count as future bookings.

    Raises:
        TypeError: if now or any start time is not a datetime.
        ValueError: if the student already holds two future bookings.
    """
    _require_datetime(now, "now")
    for start in existing_starts:
        _require_datetime(start, "existing start")
    future = sum(1 for start in existing_starts if start > now)
    if future >= MAX_FUTURE_BOOKINGS:
        raise ValueError(f"at most {MAX_FUTURE_BOOKINGS} future bookings are allowed")


def check_cancellation(start, now):
    """Check that a booking can still be cancelled (US-05 / PS-05).

    Cancelling is allowed up to and including 15 minutes before the start.

    Raises:
        TypeError: if start or now is not a datetime.
        ValueError: if fewer than 15 minutes remain before the start.
    """
    _require_datetime(start, "start")
    _require_datetime(now, "now")
    if now > start - CANCEL_CUTOFF:
        raise ValueError("bookings can be cancelled up to 15 minutes before they start")

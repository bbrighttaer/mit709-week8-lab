"""StudySpace booking rules. Do not edit.

check_duration       US-03 / PS-03: a booking lasts 30 to 120 minutes
check_booking_limit  US-04 / PS-04: at most two future bookings per student

Each check raises ValueError when the rule says no.
"""


def check_duration(start, end):
    """Raise ValueError unless the booking lasts 30 to 120 minutes."""
    minutes = (end - start).total_seconds() / 60
    if minutes < 30 or minutes > 120:
        raise ValueError(f"booking must be 30 to 120 minutes, not {int(minutes)}")


def check_booking_limit(bookings, student_email, now):
    """Raise ValueError if the student already holds two future bookings."""
    future = [b for b in bookings if b["student_email"] == student_email and b["start"] > now]
    if len(future) >= 2:
        raise ValueError("at most 2 future bookings are allowed")

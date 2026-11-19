"""StudySpace bookings (US-03, US-04).

Task 1: add telemetry to create_booking, following telemetry-spec.md.
"""
import secrets

import booking_rules


def create_booking(bookings, student_email, room, start, end, now):
    """Check the booking rules, then add a new booking to the list.

    bookings is a list of dicts, one per booking.
    Returns the new booking's id and its check-in code.
    Raises ValueError if a booking rule says no.
    """
    booking_rules.check_duration(start, end)
    booking_rules.check_booking_limit(bookings, student_email, now)
    booking_id = len(bookings) + 1
    code = secrets.token_hex(8)
    bookings.append({
        "id": booking_id,
        "room": room,
        "student_email": student_email,
        "start": start,
        "end": end,
        "checkin_code": code,
    })
    return booking_id, code

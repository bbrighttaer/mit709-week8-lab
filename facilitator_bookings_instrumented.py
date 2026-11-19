"""Reference answer for Task 1. FACILITATOR FILE: do not give to students until they are stuck.

Copy over bookings.py to make test_telemetry.py pass.
"""
import secrets
import time

import booking_rules
import telemetry


def create_booking(bookings, student_email, room, start, end, now):
    """Check the booking rules, then add a new booking to the list.

    bookings is a list of dicts, one per booking.
    Returns the new booking's id and its check-in code.
    Raises ValueError if a booking rule says no.
    """
    started = time.perf_counter()
    try:
        booking_rules.check_duration(start, end)
        booking_rules.check_booking_limit(bookings, student_email, now)
    except ValueError as e:
        telemetry.record("create_booking", "rejected", time.perf_counter() - started,
                         story="US-03", room=room, reason=str(e))
        raise
    except Exception as e:
        telemetry.record("create_booking", "error", time.perf_counter() - started,
                         story="US-03", room=room, error=type(e).__name__)
        raise
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
    telemetry.record("create_booking", "ok", time.perf_counter() - started,
                     story="US-03", room=room, booking_id=booking_id)
    return booking_id, code

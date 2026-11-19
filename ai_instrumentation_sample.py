"""AI-suggested telemetry for create_booking. Read it; do not use it.

MIT709 Week 8, Task 1. A TEACHING SAMPLE. It runs, but it breaks
most of the rules in telemetry-spec.md. Can you find which?
"""
import secrets
import time

import booking_rules
import telemetry


def create_booking(bookings, student_email, room, start, end, now):
    started = time.time()
    try:
        booking_rules.check_duration(start, end)
        booking_rules.check_booking_limit(bookings, student_email, now)
        booking_id = len(bookings) + 1
        code = secrets.token_hex(8)
        bookings.append({"id": booking_id, "room": room, "student_email": student_email,
                         "start": start, "end": end, "checkin_code": code})
        telemetry.record("create_booking", "ok", time.time() - started,
                         student=student_email, code=code)
        return booking_id, code
    except Exception as e:
        telemetry.record("create_booking", "error", 0, message=str(e))
        return None, None

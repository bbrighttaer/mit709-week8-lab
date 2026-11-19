"""AI-suggested instrumentation for create_booking (US-03, US-04 / PS-03, PS-04).

MIT709 Week 8, lab Task 1. This is a TEACHING SAMPLE. 
Read it; do not use it. It runs, and it produces logs and metrics, but
it breaks several of the rules in telemetry-spec.md.
"""
import logging
import time
from datetime import datetime

from prometheus_client import Counter, Histogram

import booking_rules
from booking_store import make_checkin_code

log = logging.getLogger("studyspace")

BOOKINGS = Counter("bookings_total", "Number of bookings", ["student", "room", "status"])
LATENCY = Histogram("booking_latency_seconds", "Booking latency")


def create_booking(conn, student_email, room_id, start, end, now):
    """Create a booking and record logs and metrics."""
    started = time.time()
    try:
        booking_rules.check_duration(start, end)
        rows = conn.execute(
            "SELECT start FROM bookings WHERE student_email = ?", (student_email,)
        ).fetchall()
        booking_rules.check_booking_limit([datetime.fromisoformat(r[0]) for r in rows], now)
        code = make_checkin_code()
        cur = conn.execute(
            "INSERT INTO bookings (room_id, student_email, start, end, checkin_code) "
            "VALUES (?, ?, ?, ?, ?)",
            (room_id, student_email, start.isoformat(), end.isoformat(), code),
        )
        conn.commit()
        LATENCY.observe(time.time() - started)
        BOOKINGS.labels(student=student_email, room=str(room_id), status="success").inc()
        log.info(f"Booking {cur.lastrowid} created for {student_email} in room {room_id}, code {code}")
        return cur.lastrowid, code
    except Exception as e:
        BOOKINGS.labels(student=student_email, room=str(room_id), status="error").inc()
        log.error(f"Booking failed for {student_email}: {e}")
        return None, None

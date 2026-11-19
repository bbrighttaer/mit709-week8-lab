"""StudySpace booking store (reference version from the Week 4 lab).

MIT709 Week 5 practical lab. This is the fixed booking store from Week 4:
all 15 acceptance and security tests in test_booking_store.py pass. Use your
own Week 4 booking_store.py instead if it also passes all 15 tests.

Traceability:
    get_sso_client_secret  US-01 / PS-01
    search_rooms           US-02 / PS-02
    create_booking         US-03, US-04 / PS-03, PS-04
    make_checkin_code      US-07 / PS-07
    export_usage_report    US-09 / PS-09
"""
import csv
import logging
import os
import re
import secrets
from datetime import datetime
from pathlib import Path

import booking_rules

log = logging.getLogger("studyspace")

SSO_CLIENT_ID = "studyspace-web"
MAX_CAPACITY = 50
REPORT_NAME = re.compile(r"[A-Za-z0-9_-]{1,40}\.csv")


def get_sso_client_secret():
    """Return the client secret StudySpace uses to sign students in (US-01 / PS-01).

    Raises:
        RuntimeError: if the secret is not set in the environment.
    """
    secret = os.environ.get("STUDYSPACE_SSO_CLIENT_SECRET")
    if not secret:
        raise RuntimeError("STUDYSPACE_SSO_CLIENT_SECRET is not set")
    return secret


def create_schema(conn):
    """Create the rooms and bookings tables."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY,
            building TEXT NOT NULL,
            name TEXT NOT NULL,
            capacity INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            room_id INTEGER NOT NULL REFERENCES rooms(id),
            student_email TEXT NOT NULL,
            start TEXT NOT NULL,
            end TEXT NOT NULL,
            checkin_code TEXT NOT NULL
        );
        """
    )


def add_room(conn, building, name, capacity):
    """Add a study room (library staff set-up)."""
    cur = conn.execute(
        "INSERT INTO rooms (building, name, capacity) VALUES (?, ?, ?)",
        (building, name, capacity),
    )
    conn.commit()
    return cur.lastrowid


def search_rooms(conn, building, min_capacity):
    """List rooms in a building with at least min_capacity seats (US-02 / PS-02).

    Raises:
        TypeError: if building is not text or min_capacity is not an integer.
        ValueError: if min_capacity is outside 1 to 50.
    """
    if not isinstance(building, str):
        raise TypeError("building must be text")
    if not isinstance(min_capacity, int) or isinstance(min_capacity, bool):
        raise TypeError("min_capacity must be an integer")
    if not 1 <= min_capacity <= MAX_CAPACITY:
        raise ValueError(f"min_capacity must be 1 to {MAX_CAPACITY}")
    return conn.execute(
        "SELECT id, building, name, capacity FROM rooms "
        "WHERE building = ? AND capacity >= ? ORDER BY name",
        (building, min_capacity),
    ).fetchall()


def make_checkin_code():
    """Make the code shown in a booking's check-in QR code (US-07 / PS-07)."""
    return secrets.token_urlsafe(16)


def create_booking(conn, student_email, room_id, start, end, now):
    """Create a booking after checking the booking rules (US-03, US-04 / PS-03, PS-04).

    Returns the new booking's id and its check-in code.
    """
    booking_rules.check_duration(start, end)
    rows = conn.execute(
        "SELECT start FROM bookings WHERE student_email = ?", (student_email,)
    ).fetchall()
    existing = [datetime.fromisoformat(row[0]) for row in rows]
    booking_rules.check_booking_limit(existing, now)
    code = make_checkin_code()
    cur = conn.execute(
        "INSERT INTO bookings (room_id, student_email, start, end, checkin_code) "
        "VALUES (?, ?, ?, ?, ?)",
        (room_id, student_email, start.isoformat(), end.isoformat(), code),
    )
    conn.commit()
    log.info("Booking %s created for room %s", cur.lastrowid, room_id)
    return cur.lastrowid, code


def export_usage_report(conn, building, day, filename, reports_dir="reports"):
    """Write one building's bookings for one day to a CSV file (US-09 / PS-09).

    day is a date string such as "2026-11-10". Returns the path written.

    Raises:
        ValueError: if filename is not a plain name ending in .csv.
    """
    if not isinstance(filename, str) or not REPORT_NAME.fullmatch(filename):
        raise ValueError("filename must be letters, digits, - or _ and end in .csv")
    folder = Path(reports_dir).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    path = (folder / filename).resolve()
    if path.parent != folder:
        raise ValueError("report must be written inside the reports folder")
    rows = conn.execute(
        "SELECT b.id, r.name, b.start, b.end FROM bookings b "
        "JOIN rooms r ON r.id = b.room_id "
        "WHERE r.building = ? AND b.start LIKE ? ORDER BY b.start",
        (building, f"{day}%"),
    ).fetchall()
    with open(path, "w", newline="", encoding="utf-8") as report:
        writer = csv.writer(report)
        writer.writerow(["booking_id", "room", "start", "end"])
        writer.writerows(rows)
    return str(path)

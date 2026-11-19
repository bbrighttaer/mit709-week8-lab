"""StudySpace daily usage report (US-09 / PS-09).

MIT709 Week 8 practical lab: the Week 7 reference version, after the review
fixes and the refactoring. Use your own Week 7 usage_report.py instead if it
passes all 11 tests in test_usage_report.py.

Behaviour changes (each made with a failing test first):
    RV-01  a booking counts only if it starts on the report's date
    RV-02  a check-in counts up to and including 15 minutes after the start (PS-06)
    RV-03  the report holds no student emails (PS-09 does not ask for them)
Refactoring (no behaviour change; equivalence_check.py reports 0 differences
against facilitator_usage_report_fixed.py):
    RV-04, RV-05, RV-10  one long function split into named helpers

A booking is a dict with the keys id, room, student_email, start, end and
checked_in_at (a datetime, or None if nobody checked in).
A room is a dict with the keys name, building and capacity.
"""
from datetime import timedelta

CHECK_IN_WINDOW = timedelta(minutes=15)  # PS-06
COUNTERS = ("bookings", "booked_minutes", "check_ins", "no_shows")
COLUMN_WIDTHS = (10, 10, 9, 11)


def build_daily_report(bookings, rooms, building, day):
    """Summarise one building's bookings for one day (US-09 / PS-09).

    Returns a dict with one row per room in the building, the totals and the
    hour in which most bookings start (None if there are no bookings).
    Bookings with missing or malformed fields are skipped (see TD-01).
    """
    rows = {room["name"]: _empty_row(room["name"]) for room in rooms if room["building"] == building}
    starts_per_hour = {}
    for booking in bookings:
        try:
            _record(booking, rows, starts_per_hour, day)
        except (KeyError, TypeError, AttributeError):
            continue
    ordered = [rows[name] for name in sorted(rows)]
    return {
        "building": building,
        "day": str(day),
        "rooms": ordered,
        "totals": {key: sum(row[key] for row in ordered) for key in COUNTERS},
        "peak_hour": _peak_hour(starts_per_hour),
    }


def format_report(report):
    """Return the report as fixed-width text, one line per room plus a total."""
    lines = [
        f"Usage report: {report['building']} on {report['day']}",
        "Room      Bookings  Minutes  Check-ins  No-shows",
    ]
    lines.extend(_format_row(row["room"], row) for row in report["rooms"])
    lines.append(_format_row("TOTAL", report["totals"]))
    if report["peak_hour"] is not None:
        lines.append(f"Peak hour: {report['peak_hour']}:00")
    return "\n".join(lines) + "\n"


def _empty_row(name):
    return {"room": name, "bookings": 0, "booked_minutes": 0, "check_ins": 0, "no_shows": 0}


def _record(booking, rows, starts_per_hour, day):
    """Add one booking to its room's row if it belongs in this report."""
    if booking["room"] not in rows or booking["start"].date() != day:
        return
    minutes = (booking["end"] - booking["start"]).total_seconds() / 60
    if minutes <= 0:
        return
    row = rows[booking["room"]]
    row["bookings"] += 1
    row["booked_minutes"] += int(minutes)
    row["check_ins" if _checked_in(booking) else "no_shows"] += 1
    hour = booking["start"].hour
    starts_per_hour[hour] = starts_per_hour.get(hour, 0) + 1


def _checked_in(booking):
    """True if somebody checked in within the PS-06 window."""
    checked_in_at = booking["checked_in_at"]
    return checked_in_at is not None and checked_in_at - booking["start"] <= CHECK_IN_WINDOW


def _peak_hour(starts_per_hour):
    """The earliest hour with the most booking starts, or None."""
    if not starts_per_hour:
        return None
    return min(starts_per_hour, key=lambda hour: (-starts_per_hour[hour], hour))


def _format_row(label, counts):
    cells = [label] + [str(counts[key]) for key in COUNTERS]
    padded = [cell.ljust(width) for cell, width in zip(cells, COLUMN_WIDTHS)]
    return "".join(padded) + cells[-1]

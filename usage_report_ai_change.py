"""StudySpace daily usage report: an AI's "easier to read" version.

MIT709 Week 8, Task 3. A TEACHING SAMPLE written to look like typical
AI-generated code; it did not come from a named model. It gives the same
results as usage_report.py. Is it as fast?
"""


def build_daily_report(bookings, day):
    """Count each room's bookings and booked minutes on one day."""
    rooms = sorted({booking["room"] for booking in bookings})
    report = {}
    for room in rooms:
        room_bookings = [b for b in bookings if b["room"] == room and b["start"].date() == day]
        if room_bookings:
            report[room] = {
                "bookings": len(room_bookings),
                "minutes": sum(int((b["end"] - b["start"]).total_seconds() // 60) for b in room_bookings),
            }
    return report

"""StudySpace daily usage report for library staff (US-09 / PS-09)."""


def build_daily_report(bookings, day):
    """Count each room's bookings and booked minutes on one day.

    bookings is a list of dicts with the keys room, start and end.
    Returns a dict: room name -> {"bookings": n, "minutes": m}, in room order.
    """
    report = {}
    for booking in bookings:
        if booking["start"].date() != day:
            continue
        row = report.setdefault(booking["room"], {"bookings": 0, "minutes": 0})
        row["bookings"] += 1
        row["minutes"] += int((booking["end"] - booking["start"]).total_seconds() // 60)
    return dict(sorted(report.items()))

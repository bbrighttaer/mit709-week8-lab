"""Performance benchmark for the StudySpace daily usage report (US-09 / PS-09).

MIT709 Week 8 practical lab, Task 3. Do not edit. Times build_daily_report on
a busy day: 3,000 bookings across 40 rooms. Choose the file with --module
(always pass it, because the default module is booking_store):

    pytest bench_usage_report.py --module usage_report --benchmark-autosave
    pytest bench_usage_report.py --module usage_report_ai_change --benchmark-compare --benchmark-compare-fail=mean:25%
"""
import random
from datetime import date, datetime, timedelta

DAY = date(2026, 11, 10)
ROOMS = [{"name": f"L{n:02d}", "building": "Library", "capacity": 6} for n in range(1, 41)]


def busy_day(count=3000, seed=8):
    rng = random.Random(seed)
    bookings = []
    for booking_id in range(1, count + 1):
        start = datetime(DAY.year, DAY.month, DAY.day, rng.randint(8, 20), rng.choice([0, 30]))
        late = rng.choice([None, 0, 5, 15, 20])
        bookings.append({
            "id": booking_id,
            "room": rng.choice(ROOMS)["name"],
            "student_email": "hidden",
            "start": start,
            "end": start + timedelta(minutes=rng.choice([30, 60, 90, 120])),
            "checked_in_at": None if late is None else start + timedelta(minutes=late),
        })
    return bookings


def test_bench_build_daily_report(store, benchmark):
    bookings = busy_day()
    report = benchmark(store.build_daily_report, bookings, ROOMS, "Library", DAY)
    assert report["totals"]["bookings"] == 3000

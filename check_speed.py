"""Check that a new version of the usage report is correct and fast enough (rule CI-16). Do not edit.

Usage:
    python check_speed.py usage_report usage_report_ai_change

Both versions run on the same 5,000 fictional bookings, on the same machine,
one after the other, so machine noise affects them alike. The best of five
timings is used for each.
"""
import json
import random
import sys
import timeit
from datetime import date, datetime, timedelta
from importlib import import_module
from pathlib import Path

LIMIT = 1.25  # CI-16: the new version may be at most 25% slower
DAY = date(2026, 11, 10)


def fictional_bookings():
    rng = random.Random(16)
    rooms = [f"R{n:02d}" for n in range(1, 9)]
    bookings = []
    for _ in range(5000):
        start = datetime(2026, 11, 1, 8) + timedelta(days=rng.randrange(14), hours=rng.randrange(10))
        bookings.append({"room": rng.choice(rooms), "start": start, "end": start + timedelta(minutes=60)})
    return bookings


def best_ms(module, bookings):
    times = timeit.repeat(lambda: module.build_daily_report(bookings, DAY), number=10, repeat=5)
    return min(times) / 10 * 1000


def main():
    old_name, new_name = sys.argv[1], sys.argv[2]
    old, new = import_module(old_name), import_module(new_name)
    bookings = fictional_bookings()
    same = old.build_daily_report(bookings, DAY) == new.build_daily_report(bookings, DAY)
    old_ms, new_ms = best_ms(old, bookings), best_ms(new, bookings)
    ratio = new_ms / old_ms
    passed = same and ratio <= LIMIT
    print(f"Same results:  {'yes' if same else 'NO'}")
    print(f"{old_name}: {old_ms:.2f} ms")
    print(f"{new_name}: {new_ms:.2f} ms")
    print(f"New version is {ratio:.1f} times the time of the old one (limit {LIMIT})")
    print(f"CI-16: {'PASS' if passed else 'FAIL'}")
    Path("reports").mkdir(exist_ok=True)
    result = {"same": same, "old_ms": round(old_ms, 2), "new_ms": round(new_ms, 2), "ratio": round(ratio, 2), "passed": passed}
    Path("reports/speed.json").write_text(json.dumps(result))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()

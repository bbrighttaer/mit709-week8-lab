"""Drive StudySpace with fictional traffic and summarise its telemetry. Do not edit.

MIT709 Week 8 practical lab. Sends a day's worth of made-up booking requests
(fictional students; some break PS-03 or PS-04, a few are malformed) and some
usage-report requests through your instrumented code, then reads the events
back and prints the RED signals for each operation: Rate (requests), Errors
and Duration (percentiles).

Usage:
    python simulate_load.py
    python simulate_load.py --requests 1000 --seed 3

Writes reports/events.jsonl, reports/metrics.prom and reports/red-summary.json.
"""
import argparse
import json
import random
import sqlite3
import statistics
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import booking_store
import telemetry
import usage_report

DAY = date(2026, 11, 10)
NOW = datetime(2026, 11, 9, 18, 0)  # requests arrive the evening before
ROOMS = [("Library", f"L1.0{n}", 4 + n) for n in range(1, 7)] + [("Science", f"S1.1{n}", 6) for n in range(4)]


def make_store():
    conn = sqlite3.connect(":memory:")
    booking_store.create_schema(conn)
    for building, name, capacity in ROOMS:
        booking_store.add_room(conn, building, name, capacity)
    return conn


def send_bookings(conn, rng, requests):
    students = [f"s{n:07d}@student.example.edu" for n in range(1, 151)]  # fictional
    for _ in range(requests):
        start = datetime(DAY.year, DAY.month, DAY.day, rng.randint(8, 18), rng.choice([0, 30]))
        kind = rng.random()
        if kind < 0.03:
            minutes, start_arg = 60, start.isoformat()  # malformed: text, not a datetime
        elif kind < 0.13:
            minutes, start_arg = rng.choice([15, 20, 150, 180]), start  # breaks PS-03
        else:
            minutes, start_arg = rng.choice([30, 60, 90, 120]), start
        try:
            booking_store.create_booking(
                conn, rng.choice(students), rng.randint(1, len(ROOMS)), start_arg,
                start + timedelta(minutes=minutes), NOW,
            )
        except (ValueError, TypeError):
            pass  # the instrumentation has already recorded the outcome


def send_reports(conn, rng, requests):
    rooms = [{"name": name, "building": building, "capacity": cap} for building, name, cap in ROOMS]
    bookings = []
    for booking_id, room_id, start, end in conn.execute("SELECT id, room_id, start, end FROM bookings"):
        start = datetime.fromisoformat(start)
        late = rng.choice([None, 0, 5, 10, 15, 25])
        bookings.append({
            "id": booking_id, "room": rooms[room_id - 1]["name"], "student_email": "hidden",
            "start": start, "end": datetime.fromisoformat(end),
            "checked_in_at": None if late is None else start + timedelta(minutes=late),
        })
    for _ in range(requests):
        usage_report.build_daily_report(bookings, rooms, rng.choice(["Library", "Science"]), DAY)


def percentile(values, p):
    if len(values) < 2:
        return values[0] if values else 0.0
    return statistics.quantiles(values, n=100, method="inclusive")[p - 1]


def summarise(events):
    summary = {}
    for operation in sorted({e["operation"] for e in events}):
        mine = [e for e in events if e["operation"] == operation]
        durations = [e["duration_ms"] for e in mine]
        outcomes = [e["outcome"] for e in mine]
        summary[operation] = {
            "requests": len(mine),
            "ok": outcomes.count("ok"),
            "rejected": outcomes.count("rejected"),
            "errors": outcomes.count("error"),
            "error_ratio": round(outcomes.count("error") / len(mine), 4),
            "p50_ms": round(percentile(durations, 50), 3),
            "p95_ms": round(percentile(durations, 95), 3),
            "p99_ms": round(percentile(durations, 99), 3),
        }
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--requests", type=int, default=400, help="booking requests to send (default 400)")
    parser.add_argument("--seed", type=int, default=8)
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    handler = telemetry.configure(out / "events.jsonl")
    rng = random.Random(args.seed)
    conn = make_store()
    send_bookings(conn, rng, args.requests)
    send_reports(conn, rng, max(1, args.requests // 20))
    handler.close()

    lines = (out / "events.jsonl").read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in lines if line.strip()]
    if not events:
        print("No telemetry events were recorded. Instrument create_booking and build_daily_report first (Task 1).")
        return 1
    summary = summarise(events)
    (out / "red-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "metrics.prom").write_text(telemetry.metrics_text(), encoding="utf-8")

    print(f"{'Operation':<20}{'Requests':>9}{'OK':>6}{'Rejected':>10}{'Errors':>8}{'p50 ms':>9}{'p95 ms':>9}{'p99 ms':>9}")
    for operation, s in summary.items():
        print(f"{operation:<20}{s['requests']:>9}{s['ok']:>6}{s['rejected']:>10}{s['errors']:>8}"
              f"{s['p50_ms']:>9.3f}{s['p95_ms']:>9.3f}{s['p99_ms']:>9.3f}")
    print(f"\nWrote {len(events)} events to {out / 'events.jsonl'}, plus metrics.prom and red-summary.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

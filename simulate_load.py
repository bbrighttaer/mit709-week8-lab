"""Send 400 fictional booking requests through create_booking and print the RED summary. Do not edit.

Run it after Task 1: python simulate_load.py
RED = Rate (requests), Errors, Duration (p50, p95 and p99 in milliseconds).
"""
import json
import random
import statistics
from datetime import datetime, timedelta
from pathlib import Path

import telemetry
from bookings import create_booking

NOW = datetime(2026, 11, 10, 8, 0)
ROOMS = ["L1.01", "L1.02", "L2.01", "S1.10"]
STUDENTS = [f"s{n:07d}@student.example.edu" for n in range(1, 201)]  # fictional


def send_requests():
    rng = random.Random(8)
    bookings = []
    for _ in range(400):
        start = NOW + timedelta(hours=rng.randrange(1, 48))
        end = start + timedelta(minutes=rng.choice([20, 30, 60, 90, 120, 180]))
        if rng.random() < 0.03:
            start = start.isoformat()  # a faulty app sends text instead of a datetime
        try:
            create_booking(bookings, rng.choice(STUDENTS), rng.choice(ROOMS), start, end, NOW)
        except (ValueError, TypeError):
            pass


def main():
    telemetry.EVENTS_FILE.unlink(missing_ok=True)  # start a fresh log
    send_requests()
    ms = telemetry.durations.get("create_booking", [])
    if not ms:
        print("No events recorded: create_booking does not call telemetry.record yet.")
        return
    cuts = statistics.quantiles(ms, n=100)
    summary = {
        "operation": "create_booking",
        "requests": len(ms),
        "ok": telemetry.count("create_booking", "ok"),
        "rejected": telemetry.count("create_booking", "rejected"),
        "errors": telemetry.count("create_booking", "error"),
        "p50_ms": round(cuts[49], 3),
        "p95_ms": round(cuts[94], 3),
        "p99_ms": round(cuts[98], 3),
    }
    print("Operation       Requests   OK  Rejected  Errors  p50 ms  p95 ms  p99 ms")
    print("create_booking  {requests:8}  {ok:3}  {rejected:8}  {errors:6}  {p50_ms:6.3f}  {p95_ms:6.3f}  {p99_ms:6.3f}".format(**summary))
    Path("reports/red-summary.json").write_text(json.dumps(summary))


if __name__ == "__main__":
    main()

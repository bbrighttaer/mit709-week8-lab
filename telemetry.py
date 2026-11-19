"""StudySpace telemetry helper. Do not edit.

Each call to record() keeps three things (see telemetry-spec.md):
    one event     a line of JSON added to reports/events.jsonl (the log)
    one count     how many calls ended with each outcome (a metric)
    one duration  how long the call took, in milliseconds (a metric)
"""
import json
from pathlib import Path

OUTCOMES = ("ok", "rejected", "error")
EVENTS_FILE = Path("reports") / "events.jsonl"

events = []     # every event recorded since the program started
counts = {}     # (operation, outcome) -> number of calls
durations = {}  # operation -> list of durations in milliseconds


def record(operation, outcome, seconds, **fields):
    """Record one call of an operation.

    operation  the function's name, for example "create_booking"
    outcome    "ok", "rejected" (a booking rule said no) or "error" (anything else failed)
    seconds    how long the call took, measured with time.perf_counter()
    fields     safe extra details, for example story="US-03" or room="L1.01".
               Never an email address or a check-in code.
    """
    if outcome not in OUTCOMES:
        raise ValueError(f"outcome must be one of {OUTCOMES}, not {outcome!r}")
    ms = round(seconds * 1000, 3)
    event = {"operation": operation, "outcome": outcome, "ms": ms, **fields}
    events.append(event)
    counts[(operation, outcome)] = counts.get((operation, outcome), 0) + 1
    durations.setdefault(operation, []).append(ms)
    EVENTS_FILE.parent.mkdir(exist_ok=True)
    with open(EVENTS_FILE, "a", encoding="utf-8") as log:
        log.write(json.dumps(event, default=str) + "\n")


def count(operation, outcome):
    """Return how many calls of operation ended with outcome."""
    return counts.get((operation, outcome), 0)

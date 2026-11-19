"""StudySpace telemetry helpers. Do not edit.

MIT709 Week 8 practical lab. One call to record() produces the three things
every instrumented operation needs (rules TM-01 to TM-06 in telemetry-spec.md):

    one structured event   a JSON log line on the "studyspace.events" logger
    one count              studyspace_operations_total{operation, outcome}
    one duration           studyspace_operation_duration_seconds{operation}

The counter and the histogram give the RED signals for each operation:
Rate (count over time), Errors (count where outcome="error") and Duration.
"""
import json
import logging
import time

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest

OUTCOMES = ("ok", "rejected", "error")
LABELS = ("operation", "outcome")  # TM-06: the only metric labels allowed

REGISTRY = CollectorRegistry()
OPERATIONS = Counter(
    "studyspace_operations",
    "StudySpace operations, by operation and outcome",
    LABELS,
    registry=REGISTRY,
)
DURATION = Histogram(
    "studyspace_operation_duration_seconds",
    "Time taken by StudySpace operations, in seconds",
    ["operation"],
    buckets=(0.0001, 0.00025, 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1),
    registry=REGISTRY,
)
EVENTS = logging.getLogger("studyspace.events")


class JsonFormatter(logging.Formatter):
    """Format a log record as one JSON object per line, with the time in UTC."""

    converter = time.gmtime

    def format(self, record):
        event = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S") + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "event": record.getMessage(),
        }
        event.update(getattr(record, "fields", {}))
        return json.dumps(event, default=str, sort_keys=True)


def configure(path=None):
    """Send events to a file (one JSON line each), or to the console if path is None."""
    handler = logging.FileHandler(path, mode="w", encoding="utf-8") if path else logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    EVENTS.handlers = [handler]
    EVENTS.setLevel(logging.INFO)
    EVENTS.propagate = False  # write each event once, not also to the root logger
    return handler


def record(operation, outcome, seconds, **fields):
    """Record one call of an operation: one event, one count and one duration.

    operation  the function name, for example "create_booking"
    outcome    "ok", "rejected" (a booking rule said no) or "error" (anything else failed)
    seconds    how long the call took, from time.perf_counter()
    fields     safe context for the event, for example room_id=3 or story="US-03".
               Never pass an email address or a check-in code (TM-05).
    """
    if outcome not in OUTCOMES:
        raise ValueError(f"outcome must be one of {OUTCOMES}, not {outcome!r}")
    OPERATIONS.labels(operation=operation, outcome=outcome).inc()
    DURATION.labels(operation=operation).observe(seconds)
    level = logging.ERROR if outcome == "error" else logging.INFO
    event = {"operation": operation, "outcome": outcome, "duration_ms": round(seconds * 1000, 3)}
    event.update(fields)
    EVENTS.log(level, operation, extra={"fields": event})


def count(operation, outcome):
    """Return how many calls of operation ended with outcome (0 if none yet)."""
    value = REGISTRY.get_sample_value(
        "studyspace_operations_total", {"operation": operation, "outcome": outcome}
    )
    return int(value or 0)


def durations_recorded(operation):
    """Return how many durations have been recorded for operation."""
    value = REGISTRY.get_sample_value("studyspace_operation_duration_seconds_count", {"operation": operation})
    return int(value or 0)


def metrics_text():
    """Return all metrics in the Prometheus text format."""
    return generate_latest(REGISTRY).decode("utf-8")

# StudySpace telemetry rules (TM-01 to TM-04)

Add telemetry to `create_booking` in `bookings.py`. Use `telemetry.record(operation, outcome, seconds, **fields)`. Do not edit `telemetry.py`.

| Rule | What the code must do | Why |
|---|---|---|
| TM-01 | Every call records exactly one event with `telemetry.record`, whatever happens. Time the call with `time.perf_counter()`. Add `story="US-03"` and `room`, plus `booking_id` when the booking is made. | One event per call is what you count and time. |
| TM-02 | The outcome is `"ok"` on success, `"rejected"` when a booking rule raises `ValueError` (add `reason=str(e)`), and `"error"` for any other exception (add `error=type(e).__name__`). | A rejection means StudySpace worked. Counting it as an error hides real failures. |
| TM-03 | After recording, raise the same exception again (`raise`). Do not change what the function returns. | Telemetry must not change how the code behaves. |
| TM-04 | Never record the student's email or the check-in code. | Logs are kept and read by many people (Week 4). |

`test_telemetry.py` checks every rule.

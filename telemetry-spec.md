# StudySpace telemetry rules (TM-01 to TM-06)

These rules say what the instrumentation of StudySpace must do. Give them to the AI assistant
with your prompt, and check its code against them before you accept it. `test_telemetry.py`
checks every rule.

Instrument two operations:

- `booking_store.create_booking` (US-03, US-04 / PS-03, PS-04)
- `usage_report.build_daily_report` (US-09 / PS-09)

Use `telemetry.record(operation, outcome, seconds, **fields)` for both. Do not edit `telemetry.py`.

| Rule | Requirement | Why |
|---|---|---|
| TM-01 | Every call records exactly one event, one count and one duration through `telemetry.record`, whatever the outcome. The event carries the story ID (`story="US-03"` for bookings, `story="US-09"` for the report) and safe context: `room_id`, and `booking_id` when a booking is created; `building` and `day` for the report. | One event per operation is the unit of analysis. The story ID keeps the PS to US to code to telemetry chain. |
| TM-02 | The outcome is `"ok"` on success, `"rejected"` when a booking rule raises `ValueError` (PS-03 length, PS-04 limit), and `"error"` for any other exception. A rejected event also holds the rule's message as `reason`; an error event holds the exception's class name as `error`. | A rejection is StudySpace working correctly. Counting it as an error hides real failures. |
| TM-03 | Instrumentation never swallows or changes an exception: after recording, the same exception is raised again. Return values are unchanged. | Telemetry must not change behaviour. All earlier tests must still pass. |
| TM-04 | The duration is measured with `time.perf_counter()` and recorded for every outcome, including rejected and error. | Slow failures are worse than fast ones. Recording only successes hides them. |
| TM-05 | No personal data or secrets in events or labels: never the student's email (PS-01 university account) and never the check-in code (PS-07). | Week 4, CWE-532. Logs are copied, kept and read by many people. |
| TM-06 | Metric labels are only `operation` and `outcome` (already set by `telemetry.record`). IDs, rooms, buildings and students never become labels. | Every distinct label value creates a new time series. Unbounded labels exhaust the metrics system. |

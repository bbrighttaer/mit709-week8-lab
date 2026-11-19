"""Mini mutation tester for the MIT709 Week 5 lab. Do not edit.

Makes one small, deliberate bug (a "mutant") in booking_rules.py at a time
and runs your test file against it. A mutant is KILLED if at least one test
fails, and SURVIVES if every test still passes. A surviving mutant is a bug
your tests would not notice.

    python mutants.py test_booking_rules_ai.py
    python mutants.py test_booking_rules.py --min-score 90

With --min-score, the script exits with an error if the mutation score is
below that percentage, so it can act as a quality gate in CI.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET = Path("booking_rules.py")

# (id, story, what the bug does, original code, mutated code)
MUTANTS = [
    ("M01", "US-03", "shortest booking becomes 25 minutes",
     "MIN_BOOKING = timedelta(minutes=30)", "MIN_BOOKING = timedelta(minutes=25)"),
    ("M02", "US-03", "a 30-minute booking is rejected",
     "if not MIN_BOOKING <= length <= MAX_BOOKING:", "if not MIN_BOOKING < length <= MAX_BOOKING:"),
    ("M03", "US-03", "a 120-minute booking is rejected",
     "if not MIN_BOOKING <= length <= MAX_BOOKING:", "if not MIN_BOOKING <= length < MAX_BOOKING:"),
    ("M04", "US-03", "longest booking becomes 125 minutes",
     "MAX_BOOKING = timedelta(minutes=120)", "MAX_BOOKING = timedelta(minutes=125)"),
    ("M05", "US-04", "a third future booking is allowed",
     "if future >= MAX_FUTURE_BOOKINGS:", "if future > MAX_FUTURE_BOOKINGS:"),
    ("M06", "US-04", "a booking starting right now counts as future",
     "if start > now)", "if start >= now)"),
    ("M07", "US-04", "the limit becomes three future bookings",
     "MAX_FUTURE_BOOKINGS = 2", "MAX_FUTURE_BOOKINGS = 3"),
    ("M08", "US-04", "past bookings count towards the limit",
     "future = sum(1 for start in existing_starts if start > now)", "future = len(existing_starts)"),
    ("M09", "US-05", "cancelling exactly 15 minutes before is refused",
     "if now > start - CANCEL_CUTOFF:", "if now >= start - CANCEL_CUTOFF:"),
    ("M10", "US-05", "the cancellation cut-off becomes 10 minutes",
     "CANCEL_CUTOFF = timedelta(minutes=15)", "CANCEL_CUTOFF = timedelta(minutes=10)"),
    ("M11", "US-05", "late cancellations are accepted",
     'raise ValueError("bookings can be cancelled up to 15 minutes before they start")', "return None"),
    ("M12", "US-03", "error message rounds minutes differently",
     "int(length.total_seconds() // 60)", "int(length.total_seconds() / 60)"),
]


def run_tests(folder, test_file):
    """Run pytest in folder; return True if every test passes."""
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", test_file],
        cwd=folder,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return result.returncode == 0


def run_with(code, test_path):
    """Run the tests against this version of booking_rules.py in a fresh folder."""
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        shutil.copy(test_path, folder / test_path.name)
        (folder / TARGET.name).write_text(code, encoding="utf-8")
        return run_tests(folder, test_path.name)


def main():
    parser = argparse.ArgumentParser(description="Mutation-test booking_rules.py.")
    parser.add_argument("test_file", help="test file to check, e.g. test_booking_rules.py")
    parser.add_argument("--min-score", type=float, default=None,
                        help="fail if the mutation score is below this percentage")
    args = parser.parse_args()

    source = TARGET.read_text(encoding="utf-8")
    test_path = Path(args.test_file)
    if not test_path.exists():
        sys.exit(f"Cannot find {test_path}")

    print(f"Mutation testing {TARGET} with {test_path.name}")
    if not run_with(source, test_path):
        sys.exit("Some tests fail on the original code. Fix them before mutation testing.")
    print("Original code: all tests pass.\n")

    killed = 0
    for mutant_id, story, what, original, mutated in MUTANTS:
        if original not in source:
            sys.exit(f"{mutant_id}: code not found. Use the provided booking_rules.py unchanged.")
        survived = run_with(source.replace(original, mutated, 1), test_path)
        killed += not survived
        status = "SURVIVED" if survived else "killed"
        print(f"{mutant_id} {story}  {what:<48} {status}")

    score = 100 * killed / len(MUTANTS)
    print(f"\nKilled {killed} of {len(MUTANTS)} mutants. Mutation score: {score:.0f}%")
    if args.min_score is not None and score < args.min_score:
        sys.exit(f"Mutation score {score:.0f}% is below the minimum of {args.min_score:.0f}%")


if __name__ == "__main__":
    main()

"""Compare two versions of usage_report.py on many random inputs.

MIT709 Week 7 practical lab. Refactoring must not change behaviour. Passing
tests are not proof of that, so this script feeds the same random bookings to
the version before your refactoring and the version after, and reports every
input on which the two disagree (a small form of differential testing).

Usage:
    python equivalence_check.py usage_report_before.py usage_report.py
    python equivalence_check.py usage_report_before.py usage_report.py --runs 5000 --seed 3

Exit code 0 means no differences were found; 1 means at least one.
"""
import argparse
import copy
import importlib.util
import random
import sys
from datetime import date, datetime, timedelta

DAY = date(2026, 11, 10)
BUILDINGS = ["Library", "Science"]
ROOM_NAMES = ["L1.01", "L1.02", "L2.01", "S1.10", "S2.20"]
DAY_OFFSETS = [0, 0, 0, 0, 1, -1, 30, -31]  # 30 and -31 give the same day number in another month
CHECK_INS = [None, -5, 0, 5, 14, 15, 16, 40]  # minutes after the start; None means no check-in
DURATIONS = [30, 60, 90, 120, 0, -30]


def load(path):
    """Import a Python file as a module, whatever its name."""
    spec = importlib.util.spec_from_file_location(path.replace(".py", "").replace("/", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def random_case(rng):
    """Return (bookings, rooms, building, day) with a few awkward values mixed in."""
    rooms = [
        {"name": name, "building": "Library" if name.startswith("L") else "Science", "capacity": rng.choice([2, 4, 8])}
        for name in rng.sample(ROOM_NAMES, rng.randint(0, len(ROOM_NAMES)))
    ]
    bookings = []
    for booking_id in range(1, rng.randint(0, 12) + 1):
        start = datetime(DAY.year, DAY.month, DAY.day, rng.randint(8, 21), rng.choice([0, 30]))
        start += timedelta(days=rng.choice(DAY_OFFSETS))
        check_in = rng.choice(CHECK_INS)
        booking = {
            "id": booking_id,
            "room": rng.choice(ROOM_NAMES),
            "student_email": f"s{rng.randint(1, 5):07d}@student.example.edu",
            "start": start,
            "end": start + timedelta(minutes=rng.choice(DURATIONS)),
            "checked_in_at": None if check_in is None else start + timedelta(minutes=check_in),
        }
        damage = rng.random()
        if damage < 0.04:
            del booking[rng.choice(list(booking))]  # a missing field
        elif damage < 0.08:
            booking["start"] = "2026-11-10 09:00"  # text where a datetime is expected
        bookings.append(booking)
    return bookings, rooms, rng.choice(BUILDINGS), DAY


def run(module, case):
    """Return what the module produces for one case, or the name of the exception it raises."""
    bookings, rooms, building, day = copy.deepcopy(case)
    try:
        report = module.build_daily_report(bookings, rooms, building, day)
        return report, module.format_report(report)
    except Exception as error:  # noqa: BLE001 - the kind of failure is part of the behaviour compared
        return type(error).__name__


def main():
    parser = argparse.ArgumentParser(description="Compare two versions of usage_report.py on random inputs.")
    parser.add_argument("before", help="the file as it was before refactoring")
    parser.add_argument("after", help="the refactored file")
    parser.add_argument("--runs", type=int, default=2000, help="number of random inputs (default 2000)")
    parser.add_argument("--seed", type=int, default=7, help="random seed, so a run can be repeated (default 7)")
    args = parser.parse_args()

    before, after = load(args.before), load(args.after)
    rng = random.Random(args.seed)
    differences = []
    for _ in range(args.runs):
        case = random_case(rng)
        if run(before, case) != run(after, case):
            differences.append(case)

    print(f"Compared {args.runs} random inputs: {len(differences)} differences.")
    for bookings, rooms, building, day in differences[:3]:
        case = (bookings, rooms, building, day)
        print(f"\nInput: building={building}, day={day}")
        print(f"  rooms: {[room['name'] for room in rooms]}")
        for booking in bookings:
            print(f"  booking: {booking}")
        print(f"  before: {run(before, case)}")
        print(f"  after:  {run(after, case)}")
    if differences:
        print("\nBehaviour changed. A refactoring must report 0 differences.")
        sys.exit(1)
    print("No behaviour change found on these inputs. This is evidence, not proof.")


if __name__ == "__main__":
    main()

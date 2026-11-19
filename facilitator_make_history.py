"""Build studyspace-history.bundle, the fictional git history for Week 8 Task 2.

MIT709 Week 8 facilitator file. Not for students. The history replays the
StudySpace labs of Weeks 3 to 7 using the real lab files (AI teaching samples,
then the human fixes), then adds four more weeks of small invented changes.
Commits whose message carries the trailer "AI-assisted: yes" count as
AI-assisted. All names, dates and code are fictional teaching data.

Run from the MIT709 folder:
    python week8/lab-files/facilitator_make_history.py week8/lab-files/studyspace-history.bundle
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # the MIT709 folder
AUTHOR = "StudySpace Team"
EMAIL = "team@studyspace.example"


def snap(path):
    return (ROOT / path).read_text(encoding="utf-8")


CHECK_IN_V1 = '''

def check_in(conn, booking_id, code, now):
    """Check a student in by the code on the room's QR code (US-07 / PS-07)."""
    row = conn.execute("SELECT start, checkin_code FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if row is None or not secrets.compare_digest(row[1], code):
        raise ValueError("unknown booking or wrong code")
    start = datetime.fromisoformat(row[0])
    if now < start - timedelta(minutes=5):
        raise ValueError("too early to check in")
    return True
'''

CHECK_IN_V2 = CHECK_IN_V1.replace(
    '''        raise ValueError("too early to check in")
    return True''',
    '''        raise ValueError("too early to check in")
    if now > start + timedelta(minutes=15):  # PS-06: released after 15 minutes
        raise ValueError("booking was released: check-in closed 15 minutes after the start")
    return True''')

BLOCK_V1 = '''

def block_room(conn, room_id, reason):
    """Library staff block a room for maintenance or exams (US-08 / PS-08)."""
    conn.execute("CREATE TABLE IF NOT EXISTS blocked (room_id INTEGER PRIMARY KEY, reason TEXT)")
    conn.execute("INSERT OR REPLACE INTO blocked (room_id, reason) VALUES (?, ?)", (room_id, reason))
    conn.commit()
'''

ACCESSIBLE = '''

ACCESSIBLE_FEATURES = ("height-adjustable desk", "hearing loop")


def filter_accessible(rooms, features, wanted):
    """Keep the rooms that have every wanted accessible feature (US-10 / PS-10).

    features maps a room id to the set of features it has.
    """
    unknown = set(wanted) - set(ACCESSIBLE_FEATURES)
    if unknown:
        raise ValueError(f"unknown features: {sorted(unknown)}")
    return [room for room in rooms if set(wanted) <= features.get(room[0], set())]
'''

README_V1 = "# StudySpace\n\nCampus study-room booking system (MIT709 running case study).\n"
README_V2 = README_V1 + """
## Running the tests

    python -m venv .venv
    pip install -r requirements.txt
    pytest

## Modules

- booking_rules.py: PS-03, PS-04, PS-05
- booking_store.py: PS-01, PS-02, PS-07, PS-08, PS-09, PS-10
- usage_report.py: PS-09
"""


def history():
    """Return the commits as (date, message, ai_assisted, {path: content})."""
    rules_ai = snap("week3/lab-files/facilitator_sample_ai_output.py")
    rules_human = snap("week3/lab-files/booking_rules_human.py")
    store_ai = snap("week4/lab-files/booking_store_sample.py")
    store_fixed = snap("week5/lab-files/booking_store.py")
    report_ai = snap("week7/lab-files/usage_report.py")
    rv01 = report_ai.replace('b["start"].day == day.day', 'b["start"].date() == day')
    rv02 = rv01.replace("# check-in must be within 10 minutes of the start",
                        "# PS-06: a check-in counts up to and including 15 minutes after the start").replace(
        ".total_seconds() / 60 < 15:", ".total_seconds() / 60 <= 15:")
    rv03 = rv02.replace(', "rooms": [], "students": []}', ', "rooms": []}').replace(
        '                    if b["student_email"] not in result["students"]:\n'
        '                        result["students"].append(b["student_email"])\n', "").replace(
        '    text = text + "Students: " + ", ".join(report["students"]) + "\\n"\n', "")
    store_check_in = store_fixed.replace("from datetime import datetime", "from datetime import datetime, timedelta")
    store_v1 = store_check_in + CHECK_IN_V1
    store_v2 = store_check_in + CHECK_IN_V2
    store_v3 = store_v2 + BLOCK_V1
    store_v4 = store_v3.replace(
        '"WHERE building = ? AND capacity >= ? ORDER BY name",',
        '"WHERE building = ? AND capacity >= ? "\n        "AND id NOT IN (SELECT room_id FROM blocked) ORDER BY name",').replace(
        "def search_rooms(conn, building, min_capacity):",
        "def search_rooms(conn, building, min_capacity):  # blocked rooms are hidden (PS-08)").replace(
        "    if not isinstance(building, str):",
        '    conn.execute("CREATE TABLE IF NOT EXISTS blocked (room_id INTEGER PRIMARY KEY, reason TEXT)")\n'
        "    if not isinstance(building, str):", 1)
    store_v5 = store_v4.replace("cur = conn.execute(", "cursor = conn.execute(").replace(
        "cur.lastrowid", "cursor.lastrowid")
    store_v6 = store_v5 + ACCESSIBLE
    check_in_tests = '''"""Tests for check-in (US-07 / PS-07, PS-06)."""
from datetime import datetime, timedelta

import pytest

import booking_store

NOW = datetime(2026, 11, 10, 9, 0)


def test_us07_check_in_with_the_right_code(conn):
    booking_id, code = booking_store.create_booking(conn, "s1@student.example.edu", 1, NOW, NOW + timedelta(hours=1), NOW)
    assert booking_store.check_in(conn, booking_id, code, NOW)


def test_us07_wrong_code_is_rejected(conn):
    booking_id, _ = booking_store.create_booking(conn, "s1@student.example.edu", 1, NOW, NOW + timedelta(hours=1), NOW)
    with pytest.raises(ValueError):
        booking_store.check_in(conn, booking_id, "wrong", NOW)
'''
    late_test = check_in_tests + '''

def test_ps06_check_in_after_15_minutes_is_rejected(conn):
    booking_id, code = booking_store.create_booking(conn, "s1@student.example.edu", 1, NOW, NOW + timedelta(hours=1), NOW)
    with pytest.raises(ValueError):
        booking_store.check_in(conn, booking_id, code, NOW + timedelta(minutes=16))
'''
    accessible_tests = '''"""Tests for the accessible-features filter (US-10 / PS-10)."""
import pytest

import booking_store

ROOMS = [(1, "Library", "L1.01", 4), (2, "Library", "L1.02", 8)]
FEATURES = {1: {"hearing loop"}, 2: {"hearing loop", "height-adjustable desk"}}


def test_us10_filter_keeps_rooms_with_every_feature():
    rooms = booking_store.filter_accessible(ROOMS, FEATURES, ["hearing loop", "height-adjustable desk"])
    assert [room[0] for room in rooms] == [2]


def test_us10_unknown_feature_is_rejected():
    with pytest.raises(ValueError):
        booking_store.filter_accessible(ROOMS, FEATURES, ["sofa"])
'''
    pipeline_ai = snap("week6/lab-files/ai_pipeline_sample.yml")
    pipeline_ref = snap("week7/lab-files/pipeline.yml")
    reqs = "pytest==8.4.2\npytest-cov==7.1.0\n"
    return [
        ("2026-09-14T10:02:00+10:00", "chore: start StudySpace project", False,
         {"README.md": README_V1, "requirements.txt": reqs}),
        ("2026-09-15T14:20:00+10:00", "feat: booking rules for US-03 to US-05", True,
         {"booking_rules.py": rules_ai}),
        ("2026-09-16T11:05:00+10:00", "test: acceptance tests for US-03 to US-05", False,
         {"test_booking_rules.py": snap("week3/lab-files/test_booking_rules.py"),
          "conftest.py": snap("week3/lab-files/conftest.py")}),
        ("2026-09-17T16:40:00+10:00", "fix: booking rules match PS-03 to PS-05 boundaries", False,
         {"booking_rules.py": rules_human}),
        ("2026-09-22T09:30:00+10:00", "feat: booking store with search, booking and report export", True,
         {"booking_store.py": store_ai}),
        ("2026-09-23T13:15:00+10:00", "test: acceptance and security tests for the store", False,
         {"test_booking_store.py": snap("week4/lab-files/test_booking_store.py"),
          "conftest.py": snap("week4/lab-files/conftest.py")}),
        ("2026-09-24T15:50:00+10:00", "fix: SEC-01 to SEC-05 security fixes in booking store", False,
         {"booking_store.py": store_fixed}),
        ("2026-09-29T10:10:00+10:00", "test: AI-generated unit tests for booking rules", True,
         {"test_booking_rules.py": snap("week5/lab-files/test_booking_rules_sample_ai.py")}),
        ("2026-09-30T14:45:00+10:00", "test: add boundary tests that kill surviving mutants", False,
         {"test_booking_rules.py": snap("week7/lab-files/test_booking_rules.py"),
          "mutants.py": snap("week5/lab-files/mutants.py"),
          "booking_rules.py": snap("week5/lab-files/booking_rules.py")}),
        ("2026-10-01T11:20:00+10:00", "ci: run tests with coverage and mutation gates", False,
         {".github/workflows/tests.yml": snap("week5/lab-files/tests.yml")}),
        ("2026-10-06T09:40:00+10:00", "ci: AI-drafted delivery pipeline", True,
         {".github/workflows/pipeline.yml": pipeline_ai}),
        ("2026-10-07T15:30:00+10:00", "fix(ci): pin actions by SHA and use a read-only token", False,
         {".github/workflows/pipeline.yml": pipeline_ref}),
        ("2026-10-08T10:05:00+10:00", "chore: upgrade pytest to 9.0.3 (PYSEC-2026-1845)", False,
         {"requirements.txt": "pytest==9.0.3\npytest-cov==7.1.0\n"}),
        ("2026-10-13T09:15:00+10:00", "feat: daily usage report for library staff (US-09)", True,
         {"usage_report.py": report_ai, "test_usage_report.py": snap("week7/lab-files/test_usage_report.py")}),
        ("2026-10-14T10:30:00+10:00", "fix: RV-01 count bookings by full date", False,
         {"usage_report.py": rv01}),
        ("2026-10-14T11:10:00+10:00", "fix: RV-02 check-in window is inclusive (PS-06)", False,
         {"usage_report.py": rv02}),
        ("2026-10-14T14:25:00+10:00", "fix: RV-03 remove student emails from the report", False,
         {"usage_report.py": rv03}),
        ("2026-10-15T16:00:00+10:00", "refactor: split build_daily_report into helpers", True,
         {"usage_report.py": snap("week8/lab-files/usage_report.py")}),
        ("2026-10-16T09:45:00+10:00", "ci: add complexity gate CI-14", False,
         {"ruff.toml": '[lint]\nextend-select = ["C901"]\n\n[lint.mccabe]\nmax-complexity = 10\n'}),
        ("2026-10-20T10:20:00+10:00", "feat: check in with the QR code (US-07)", True,
         {"booking_store.py": store_v1}),
        ("2026-10-21T13:35:00+10:00", "test: check-in tests", False,
         {"test_check_in.py": check_in_tests}),
        ("2026-10-23T15:05:00+10:00", "fix: close check-in 15 minutes after the start (PS-06)", False,
         {"booking_store.py": store_v2, "test_check_in.py": late_test}),
        ("2026-10-27T09:50:00+10:00", "feat: staff can block rooms (US-08)", False,
         {"booking_store.py": store_v3}),
        ("2026-10-29T14:10:00+10:00", "fix: hide blocked rooms from search (PS-08)", False,
         {"booking_store.py": store_v4}),
        ("2026-11-02T10:00:00+10:00", "docs: explain how to run the tests", True,
         {"README.md": README_V2}),
        ("2026-11-03T11:30:00+10:00", "refactor: clearer names in booking store", True,
         {"booking_store.py": store_v5}),
        ("2026-11-10T09:25:00+10:00", "feat: filter rooms by accessible features (US-10)", True,
         {"booking_store.py": store_v6}),
        ("2026-11-10T10:40:00+10:00", "test: accessible-feature filter tests", True,
         {"test_accessible.py": accessible_tests}),
    ]


def git(repo, *args, date=None):
    env = dict(os.environ, GIT_AUTHOR_NAME=AUTHOR, GIT_AUTHOR_EMAIL=EMAIL,
               GIT_COMMITTER_NAME=AUTHOR, GIT_COMMITTER_EMAIL=EMAIL)
    if date:
        env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)


def main():
    out = Path(sys.argv[1]).resolve()
    repo = Path(tempfile.mkdtemp())
    try:
        git(repo, "init", "-b", "main")
        for date, message, ai, files in history():
            for path, content in files.items():
                target = repo / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            git(repo, "add", "-A")
            body = message + ("\n\nAI-assisted: yes" if ai else "")
            git(repo, "commit", "-m", body, date=date)
        git(repo, "bundle", "create", str(out), "--all")
        print(f"Wrote {out} with {len(history())} commits.")
    finally:
        shutil.rmtree(repo)


if __name__ == "__main__":
    main()

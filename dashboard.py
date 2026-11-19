"""Print the StudySpace quality dashboard as Markdown (rule CI-15). Do not edit.

The pipeline adds it to the run's Summary page. To preview it: python dashboard.py
It reads the files in reports/ and the LINT and TESTS results set by the pipeline.
"""
import json
import os
from pathlib import Path


def load(name):
    path = Path("reports") / name
    return json.loads(path.read_text()) if path.exists() else None


def main():
    print("## StudySpace quality dashboard\n")
    print("| Check | Result |")
    print("|---|---|")
    print(f"| Lint (Ruff) | {os.environ.get('LINT', 'not run')} |")
    print(f"| Tests (pytest) | {os.environ.get('TESTS', 'not run')} |")

    red = load("red-summary.json")
    print("\n### Telemetry: create_booking under simulated load\n")
    if red:
        print("| Requests | OK | Rejected | Errors | p50 ms | p95 ms | p99 ms |")
        print("|---|---|---|---|---|---|---|")
        print(f"| {red['requests']} | {red['ok']} | {red['rejected']} | {red['errors']} | "
              f"{red['p50_ms']} | {red['p95_ms']} | {red['p99_ms']} |")
    else:
        print("No telemetry yet.")

    outcomes = load("outcomes.json")
    print("\n### AI-assisted outcomes (fictional history)\n")
    if outcomes:
        print("| Group | Commits | Median lines changed | Followed by a fix |")
        print("|---|---|---|---|")
        for name, g in outcomes.items():
            print(f"| {name} | {g['commits']} | {g['median_lines']:g} | {g['fixed']} ({g['fixed_pct']}%) |")
    else:
        print("No outcome analysis yet.")


if __name__ == "__main__":
    main()

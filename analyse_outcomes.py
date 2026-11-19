"""Compare AI-assisted and other commits in a team's history. Do not edit.

Usage: python analyse_outcomes.py commit-history.csv

Each row of the CSV file is one commit: its date, subject, kind of work,
whether it was tagged "AI-assisted: yes", how many lines it changed, and
whether a fix changed the same files within 7 days.
"""
import csv
import json
import statistics
import sys
from pathlib import Path


def summarise(commits):
    total = len(commits)
    groups = {}
    for name, tag in (("AI-assisted", "yes"), ("Not tagged", "no")):
        mine = [c for c in commits if c["ai_assisted"] == tag]
        fixed = [c for c in mine if c["fixed_within_7_days"] == "yes"]
        features = [c for c in mine if c["kind"] == "feat"]
        kinds = {}
        for c in mine:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        groups[name] = {
            "commits": len(mine),
            "share": round(100 * len(mine) / total),
            "kinds": ", ".join(f"{kind} {n}" for kind, n in sorted(kinds.items())),
            "median_lines": statistics.median(int(c["lines_changed"]) for c in mine),
            "fixed": len(fixed),
            "fixed_pct": round(100 * len(fixed) / len(mine)),
            "features_fixed": f"{sum(c in fixed for c in features)} of {len(features)}",
        }
    return groups


def main():
    with open(sys.argv[1], newline="", encoding="utf-8") as file:
        commits = list(csv.DictReader(file))
    groups = summarise(commits)
    print("| Group | Commits | Kinds of work | Median lines changed | Followed by a fix within 7 days | Features followed by a fix |")
    print("|---|---|---|---|---|---|")
    for name, g in groups.items():
        print(f"| {name} | {g['commits']} ({g['share']}%) | {g['kinds']} | {g['median_lines']:g} | "
              f"{g['fixed']} ({g['fixed_pct']}%) | {g['features_fixed']} |")
    Path("reports").mkdir(exist_ok=True)
    Path("reports/outcomes.json").write_text(json.dumps(groups))


if __name__ == "__main__":
    main()

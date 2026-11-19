"""Compare AI-assisted and other commits in a git repository. Do not edit.

MIT709 Week 8 practical lab, Task 2. Reads the history with PyDriller and,
for each group of commits, reports how many there are, what kind of work they
were, how big they were, and how often a fix followed within a few days on
the same files (a rework signal), overall and for feature commits only.

A commit counts as AI-assisted if its message has the trailer
"AI-assisted: yes", says "AI-generated", or has a Co-authored-by line naming
a known AI tool. Everything else is "not tagged", which is not the same as
"written without AI". The kind of work comes from the Conventional Commits
prefix (feat, fix, test, refactor, ci, docs, chore).

The output describes one team's history. It does not rank people: no author
names are read or reported.

Usage:
    python analyse_outcomes.py studyspace-history
    python analyse_outcomes.py ../mit709-week7-lab --days 7 --out reports
"""
import argparse
import csv
import json
import re
import statistics
import sys
from datetime import timedelta
from pathlib import Path

from pydriller import Repository

AI_TRAILER = re.compile(r"^AI-assisted:\s*yes\s*$", re.IGNORECASE | re.MULTILINE)
AI_COAUTHOR = re.compile(r"^Co-authored-by:.*(copilot|claude|cursor|codex|devin|jules|gemini)", re.IGNORECASE | re.MULTILINE)
KIND = re.compile(r"^(feat|fix|test|refactor|ci|docs|chore|perf|build|style|revert)(\(.+?\))?!?:", re.IGNORECASE)
GROUPS = ("AI-assisted", "Not tagged")


def is_ai_assisted(message):
    return bool(AI_TRAILER.search(message) or AI_COAUTHOR.search(message) or "ai-generated" in message.lower())


def read_commits(repo):
    commits = []
    for c in Repository(repo).traverse_commits():
        subject = c.msg.splitlines()[0]
        kind = KIND.match(subject)
        commits.append({
            "hash": c.hash[:7],
            "date": c.committer_date,
            "subject": subject,
            "kind": kind.group(1).lower() if kind else "other",
            "group": GROUPS[0] if is_ai_assisted(c.msg) else GROUPS[1],
            "lines": c.insertions + c.deletions,
            "files": sorted({f.new_path or f.old_path for f in c.modified_files}),
        })
    return commits


def mark_rework(commits, days):
    """Flag each commit that a fix commit touched again within `days` days."""
    window = timedelta(days=days)
    for c in commits:
        c["fixed_within"] = any(
            f is not c and f["kind"] == "fix" and c["date"] < f["date"] <= c["date"] + window
            and set(f["files"]) & set(c["files"])
            for f in commits
        )


def summarise(commits, days):
    summary = {"total_commits": len(commits), "rework_window_days": days, "groups": {}}
    for group in GROUPS:
        mine = [c for c in commits if c["group"] == group]
        if not mine:
            continue
        feats = [c for c in mine if c["kind"] == "feat"]
        kinds = {}
        for c in mine:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        summary["groups"][group] = {
            "commits": len(mine),
            "share": round(len(mine) / len(commits), 3),
            "kinds": dict(sorted(kinds.items())),
            "median_lines_changed": statistics.median(c["lines"] for c in mine),
            "followed_by_fix": sum(c["fixed_within"] for c in mine),
            "followed_by_fix_rate": round(sum(c["fixed_within"] for c in mine) / len(mine), 3),
            "feat_commits": len(feats),
            "feat_followed_by_fix": sum(c["fixed_within"] for c in feats),
        }
    return summary


def print_table(summary):
    days = summary["rework_window_days"]
    print(f"Commits analysed: {summary['total_commits']}\n")
    print(f"| Group | Commits | Kinds of work | Median lines changed | Followed by a fix within {days} days | Features followed by a fix |")
    print("|---|---|---|---|---|---|")
    for group, g in summary["groups"].items():
        kinds = ", ".join(f"{k} {n}" for k, n in g["kinds"].items())
        feats = f"{g['feat_followed_by_fix']} of {g['feat_commits']}"
        print(f"| {group} | {g['commits']} ({g['share']:.0%}) | {kinds} | {g['median_lines_changed']:g} | "
              f"{g['followed_by_fix']} ({g['followed_by_fix_rate']:.0%}) | {feats} |")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", help="path to a git repository (a folder containing .git)")
    parser.add_argument("--days", type=int, default=7, help="rework window in days (default 7)")
    parser.add_argument("--out", default="reports", help="folder for commits.csv and outcomes.json")
    args = parser.parse_args()

    commits = read_commits(args.repo)
    if not commits:
        print("No commits found.")
        return 1
    mark_rework(commits, args.days)
    summary = summarise(commits, args.days)

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    with open(out / "commits.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["hash", "date", "group", "kind", "lines", "files", "fixed_within", "subject"])
        for c in commits:
            writer.writerow([c["hash"], c["date"].isoformat(), c["group"], c["kind"], c["lines"],
                             ";".join(c["files"]), c["fixed_within"], c["subject"]])
    (out / "outcomes.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print_table(summary)
    print(f"\nWrote {out / 'commits.csv'} and {out / 'outcomes.json'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

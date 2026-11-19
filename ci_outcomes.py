"""Summarise a public repository's GitHub Actions runs. Do not edit.

MIT709 Week 8 practical lab, Task 2. Reads the workflow runs from the GitHub
REST API (GET /repos/{owner}/{repo}/actions/runs) and reports delivery
signals that stand in for two DORA metrics in a student project:

    failed-run rate      share of finished runs that failed (a change fail rate proxy)
    time back to green   time from a failed run to the next successful run of the
                         same workflow on the same branch (a recovery time proxy)

No token is needed for a public repository (GitHub allows 60 requests an hour
without one). If GITHUB_TOKEN is set, it is used.

Usage:
    python ci_outcomes.py YOUR-USERNAME/mit709-week7-lab
"""
import argparse
import json
import os
import statistics
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

API = "https://api.github.com/repos/{repo}/actions/runs?per_page=100"


def fetch_runs(repo):
    request = urllib.request.Request(API.format(repo=repo), headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "mit709-week8-lab",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310 - fixed https URL
        return json.load(response)["workflow_runs"]


def when(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")  # GitHub times are UTC


def summarise(runs):
    finished = [r for r in runs if r["status"] == "completed" and r["conclusion"] in ("success", "failure")]
    finished.sort(key=lambda r: r["created_at"])
    failed = [r for r in finished if r["conclusion"] == "failure"]
    minutes = [(when(r["updated_at"]) - when(r["run_started_at"])).total_seconds() / 60 for r in finished]
    back_to_green = []
    for i, run in enumerate(finished):
        if run["conclusion"] != "failure":
            continue
        later = [r for r in finished[i + 1:] if r["head_branch"] == run["head_branch"]
                 and r["workflow_id"] == run["workflow_id"] and r["conclusion"] == "success"]
        if later:
            back_to_green.append((when(later[0]["created_at"]) - when(run["created_at"])).total_seconds() / 60)
    return {
        "runs": len(finished),
        "failed": len(failed),
        "failed_rate": round(len(failed) / len(finished), 3) if finished else None,
        "median_run_minutes": round(statistics.median(minutes), 1) if minutes else None,
        "median_back_to_green_minutes": round(statistics.median(back_to_green), 1) if back_to_green else None,
        "recoveries": len(back_to_green),
        "by_event": {event: sum(1 for r in finished if r["event"] == event) for event in sorted({r["event"] for r in finished})},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", help="owner/name, for example YOUR-USERNAME/mit709-week7-lab")
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()
    try:
        runs = fetch_runs(args.repo)
    except urllib.error.HTTPError as error:
        print(f"GitHub said {error.code} {error.reason}. Check the name and that the repository is public.")
        return 1
    summary = summarise(runs)
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    (out / "ci-outcomes.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    def show(value, unit=""):
        return "n/a" if value is None else f"{value}{unit}"

    rate = "n/a" if summary["failed_rate"] is None else f"{summary['failed_rate']:.0%}"
    print(f"Finished runs (success or failure): {summary['runs']}  {summary['by_event']}")
    print(f"Failed runs: {summary['failed']} ({rate})")
    print(f"Median run time: {show(summary['median_run_minutes'], ' min')}")
    print(f"Median time back to green after a failure: {show(summary['median_back_to_green_minutes'], ' min')}"
          f" ({summary['recoveries']} recoveries)")
    print(f"\nWrote {out / 'ci-outcomes.json'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

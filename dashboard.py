"""Build the StudySpace quality dashboard as Markdown. Do not edit.

MIT709 Week 8 practical lab, Task 3 (pipeline rule CI-15). Reads the report
files below from the reports folder, skips any that are missing, and prints
one Markdown page. In GitHub Actions, append it to the job summary:

    python dashboard.py >> "$GITHUB_STEP_SUMMARY"

    junit.xml         pytest --junitxml
    coverage.json     pytest-cov --cov-report=json
    mutation.txt      output of mutants.py
    radon.json        radon cc -j
    red-summary.json  simulate_load.py
    benchmark.json    pytest-benchmark --benchmark-json
    outcomes.json     analyse_outcomes.py
    ci-outcomes.json  ci_outcomes.py (optional)
"""
import argparse
import json
import os
import re
import time
import xml.etree.ElementTree as ET  # nosec B405 - parses our own pytest output
from pathlib import Path

COVERAGE_TARGET = 90  # CI-03
MUTATION_TARGET = 90  # CI-04
COMPLEXITY_LIMIT = 10  # CI-14


def load_json(folder, name):
    path = folder / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def status(ok):
    return "n/a" if ok is None else ("PASS" if ok else "FAIL")


def gates(folder):
    rows = []
    junit = folder / "junit.xml"
    if junit.exists():
        suites = ET.parse(junit).getroot()  # nosec B314 - our own file
        suites = suites.findall("testsuite") if suites.tag == "testsuites" else [suites]
        total = sum(int(s.get("tests", 0)) for s in suites)
        failed = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
        rows.append(("Tests", f"{total - failed} passed, {failed} failed", "all pass (CI-03)", status(failed == 0)))
    coverage = load_json(folder, "coverage.json")
    if coverage:
        pct = coverage["totals"]["percent_covered"]
        rows.append(("Line and branch coverage", f"{pct:.1f}%", f">= {COVERAGE_TARGET}% (CI-03)", status(pct >= COVERAGE_TARGET)))
    mutation = folder / "mutation.txt"
    if mutation.exists():
        found = re.search(r"Mutation score: (\d+)%", mutation.read_text(encoding="utf-8"))
        if found:
            score = int(found.group(1))
            rows.append(("Mutation score (booking rules)", f"{score}%", f">= {MUTATION_TARGET}% (CI-04)", status(score >= MUTATION_TARGET)))
    radon = load_json(folder, "radon.json")
    if radon:
        blocks = [(b["complexity"], f"{Path(f).stem}.{b['name']}") for f, items in radon.items()
                  for item in items for b in [item, *item.get("methods", [])]]
        worst = max(blocks)
        rows.append(("Highest cyclomatic complexity", f"{worst[0]} ({worst[1]})", f"<= {COMPLEXITY_LIMIT} (CI-14)", status(worst[0] <= COMPLEXITY_LIMIT)))
    if not rows:
        return []
    out = ["### Quality gates", "", "| Signal | Value | Target (rule) | Status |", "|---|---|---|---|"]
    out += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
    return out + [""]


def runtime(folder):
    red = load_json(folder, "red-summary.json")
    if not red:
        return []
    out = ["### Runtime: RED signals from simulated load", "",
           "| Operation | Requests | Rejected (rule said no) | Errors | Error ratio | p50 ms | p95 ms | p99 ms |",
           "|---|---|---|---|---|---|---|---|"]
    for op, s in red.items():
        out.append(f"| {op} | {s['requests']} | {s['rejected']} | {s['errors']} | {s['error_ratio']:.1%} "
                   f"| {s['p50_ms']:.3f} | {s['p95_ms']:.3f} | {s['p99_ms']:.3f} |")
    return out + ["", "StudySpace has no agreed SLO yet. Choosing one is a stakeholder decision (a new PS statement).", ""]


def performance(folder):
    bench = load_json(folder, "benchmark.json")
    if not bench:
        return []
    out = ["### Performance benchmark", "", "| Benchmark | Mean ms | Std dev ms | Rounds |", "|---|---|---|---|"]
    for b in bench["benchmarks"]:
        s = b["stats"]
        out.append(f"| {b['name']} | {s['mean'] * 1000:.3f} | {s['stddev'] * 1000:.3f} | {s['rounds']} |")
    return out + ["", "Shared CI runners are noisy, so this is a trend to watch, not a gate. The regression check (CI-16) runs locally.", ""]


def delivery(folder):
    outcomes = load_json(folder, "outcomes.json")
    ci = load_json(folder, "ci-outcomes.json")
    if not outcomes and not ci:
        return []
    out = ["### Delivery and AI use", ""]
    if outcomes:
        days = outcomes["rework_window_days"]
        out += [f"| Commits | Count | Followed by a fix within {days} days | Features followed by a fix |", "|---|---|---|---|"]
        for group, g in outcomes["groups"].items():
            out.append(f"| {group} | {g['commits']} ({g['share']:.0%}) | {g['followed_by_fix']} ({g['followed_by_fix_rate']:.0%}) "
                       f"| {g['feat_followed_by_fix']} of {g['feat_commits']} |")
        out.append("")
    if ci:
        rate = "n/a" if ci["failed_rate"] is None else f"{ci['failed_rate']:.0%}"
        back = ci["median_back_to_green_minutes"]
        out += [f"Pipeline runs: {ci['runs']}, failed {ci['failed']} ({rate}); "
                + f"median time back to green: {'n/a' if back is None else back} min.", ""]
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reports", default="reports")
    folder = Path(parser.parse_args().reports)
    commit = os.environ.get("GITHUB_SHA", "local")[:7]
    stamp = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    lines = ["## StudySpace quality dashboard", "",
             f"Commit {commit}, built {stamp}. Team-level signals for one service: not for comparing people.", ""]
    body = gates(folder) + runtime(folder) + performance(folder) + delivery(folder)
    print("\n".join(lines + (body or ["No report files found in the reports folder."])))


if __name__ == "__main__":
    main()

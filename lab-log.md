# Week 8 lab log: StudySpace telemetry, outcomes and dashboard

Repository URL:
Starting point (my Week 7 files / the provided reference files):

---

## 1. Logging and metrics (Task 1)

**AI tool used** (Copilot Free chat / Google AI Studio):

**Prompt sent** (paste it):

```text

```

**Review of the AI's instrumentation against the rules.** One row per rule. "Met?" is your
judgement before running the tests; then record what `test_telemetry.py` said.

| Rule | Met by the AI's first answer? | What I changed, and why | Test result |
|---|---|---|---|
| TM-01 one event, count, duration; story ID |  |  |  |
| TM-02 ok / rejected / error |  |  |  |
| TM-03 exceptions still raised |  |  |  |
| TM-04 duration for every outcome |  |  |  |
| TM-05 no email or check-in code |  |  |  |
| TM-06 labels only operation and outcome |  |  |  |

**RED summary from `simulate_load.py`** (paste the table):

```text

```

Which StudySpace failure would these signals show first, and which would they miss? (2-3 sentences)

---

## 2. AI-assisted development outcomes (Task 2)

**Fictional team history** (`analyse_outcomes.py studyspace-history`), paste the table:

**My Week 7 repository** (`analyse_outcomes.py`), paste the table, or write "not available":

**Pipeline runs** (`ci_outcomes.py`), paste the output:

**Interpretation (150 to 250 words).** Answer: what does the evidence suggest about AI-assisted work
in this history? Name at least two reasons the comparison could mislead (for example the kind of
work, how commits were tagged, sample size, commits too recent to have been fixed). Say which
SPACE dimensions and DORA metrics your signals cover and which they miss. Propose one
perception measure you would add.

---

## 3. Quality dashboard (Task 3)

**Benchmark baseline** (mean ms, std dev ms):

**AI change benchmark** (mean ms, and how many times slower):

**Did the tests and `equivalence_check.py` catch the slowdown?**

**Decision on the AI change** (merge, reject or ask for changes) and the reason, naming US-09 / PS-09:

**Link to the pipeline run that shows the dashboard:**

**One signal you would add to the dashboard, and the decision it would help someone make:**

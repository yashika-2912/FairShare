# Phase 5 results

The repository's Phase 5 artifacts are `experiments/results.csv` (one record
per captured process) and `experiments/fairness.csv` (one Jain-index record
per workload repetition).  The summaries below are calculated from those
existing files; no workload has been rerun for this documentation.

## What is measured

- Response, waiting, turnaround, and CPU time are ticks.
- Context switches are counts.
- Jain's Fairness Index is computed over CPU ticks within each captured
  workload repetition: `(sum x)^2 / (n * sum(x^2))`.  A zero CPU-time total
  is recorded as `0.0` by the parser.

## Observed averages

The dashboard uses these same aggregation rules: it averages all available
process rows for each workload/scheduler pair, and averages the available
per-repetition fairness values.  The CSV capture is uneven for a few
single-process workloads (for example, one mixed repetition is absent for
each scheduler), so comparisons should be read as the recorded data rather
than as a balanced statistical study.

| Workload | Main observation from captured data |
| --- | --- |
| CPU-bound | Both schedulers report zero response/waiting time; FairShare has lower mean turnaround and CPU ticks (2.33 vs 3.00) and fewer switches (8.33 vs 9.00). |
| I/O-bound | Both report zero response/waiting time; FairShare is slightly lower in turnaround (60.00 vs 60.67) and switches (66.00 vs 66.33). |
| Mixed | Both report zero response/waiting time; FairShare is slightly higher in captured turnaround (40.50 vs 40.00) and switches (46.50 vs 45.50). |
| Starvation | The many recorded participants show FairShare lower mean CPU time (0.089 vs 0.224) but higher mean response, waiting, turnaround, and context switches.  Recorded mean Jain fairness is 0.029 for FairShare and 0.073 for Vanilla. |

Single-participant fairness values should not be used to compare scheduling
equity: Jain's index is trivially 1.0 for a nonzero single participant and is
0.0 when the parser observes no CPU ticks.  The starvation workload is the
meaningful multi-participant fairness case in this capture.


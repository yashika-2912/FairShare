# FairShare architecture and math

This document describes the scheduler implemented in this repository.

## Runtime flow

`clockintr()` advances the global tick count on CPU 0 while holding
`tickslock`, then invokes `fs_tick_update()`.  That function visits process
entries one at a time under their individual `p->lock` and records CPU time
for `RUNNING` processes, evaluation waiting time for `RUNNABLE` processes, and
sleep time for `SLEEPING` processes.  CPU and sleep accounting refresh the
workload class.

`scheduler()` runs per CPU in `kernel/proc.c`.  It scans runnable processes,
computes each candidate's priority, and dispatches the process with the lowest
priority value.  Ties are deliberately resolved by the existing process-table
order.  Before dispatch it records the first-run tick when needed, increments
the evaluation context-switch count, and records `last_ran_tick`.

A CPU burst begins on dispatch when `burst_start` is zero.  `sleep()` and
`kexit()` finish a burst before their state transition, updating the prediction.
The scheduler rechecks the selected process under its lock before switching,
because another CPU may have dispatched it after the scan.

## Per-process state

`struct proc` holds the policy fields below, protected by `p->lock`:

- `pred_burst`, `burst_start`: predicted and current CPU-burst timing.
- `cpu_ticks`, `sleep_ticks`, `wclass`: cumulative classification accounting.
- `last_ran_tick`, `wait_ticks`, `priority`: scheduling/aging state.
- `eval_creation_tick`, `eval_first_run_tick`, `eval_cpu_ticks`,
  `eval_wait_ticks`, `eval_context_switches`: Phase 5 measurements.  These
  metrics are not read by the scheduler's policy decision.

## Constants

| Constant | Value | Purpose |
| --- | ---: | --- |
| `ALPHA` | 50 | Actual-burst weight in the EMA |
| `SCALE` | 100 | Integer EMA scale |
| `PRED_BURST_SEED` | 10 | Initial predicted burst (ticks) |
| `IO_BONUS` | 5 | Priority reduction for I/O-bound processes |
| `IO_THRESHOLD` | 60 | I/O percentage needed for I/O-bound classification |
| `AGE_WEIGHT` | 1 | Aging priority reduction per interval |
| `AGE_INTERVAL` | 10 | Waiting ticks in one aging interval |
| `AGE_CAP` | 500 | Waiting threshold that forces priority to zero |

## Integer formulas

All arithmetic is integer arithmetic; there is no floating point in the
kernel scheduler.

```text
pred_burst = (ALPHA * actual_burst
              + (SCALE - ALPHA) * pred_burst) / SCALE

io_ratio = (sleep_ticks * 100) / (cpu_ticks + sleep_ticks + 1)

wclass = IO_BOUND  when io_ratio >= IO_THRESHOLD
         CPU_BOUND otherwise

wait_ticks = max(0, ticks - last_ran_tick)

priority = pred_burst - class_bonus
           - AGE_WEIGHT * (wait_ticks / AGE_INTERVAL)

class_bonus = IO_BONUS for IO_BOUND, otherwise 0

if wait_ticks >= AGE_CAP: priority = 0
```

Lower `priority` values have higher dispatch preference.  The `+1` in the
I/O ratio denominator prevents division by zero.  A negative elapsed time
from tick wrap is clamped to zero before it can produce an aging boost.


# FairShare design

This document records the authoritative FairShare policy for the xv6 source in
this repository. It is a Phase 1 design record only: no scheduler selection
behavior is changed here.

## Source integration points

The process fields below belong in `struct proc` in `kernel/proc.h` (the
existing state fields protected by `p->lock` begin at line 85). Process
allocation and initialization are performed by the static `allocproc()` in
`kernel/proc.c:110`, which returns with `p->lock` held. The scheduler selection
loop is `scheduler()` in `kernel/proc.c:429`; it currently scans the process
array in table order and runs each `RUNNABLE` process it encounters. That
selection is intentionally unchanged in Phase 1.

Tick accounting must use the actual tick source: `clockintr()` in
`kernel/trap.c:167`. Only CPU 0 increments the global `ticks` under
`tickslock`, then calls `wakeup(&ticks)`. Timer interrupts reach it through
`devintr()` in `kernel/trap.c:188`, which returns 2; both `usertrap()`
(`kernel/trap.c:38`) and `kerneltrap()` (`kernel/trap.c:137`) call `yield()`
for that result. The existing yield implementation is `kernel/proc.c:501`.

Sleep/wakeup state transitions occur in `sleep_prepare()` at
`kernel/proc.c:548`, `sleep()` at `kernel/proc.c:563`, and `wakeup()` at
`kernel/proc.c:577`, each using the individual process lock. Process exit is
implemented as `kexit()` in `kernel/proc.c:325` in this xv6 tree (there is no
function named `exit()`).

## Authoritative FairShare state

Add these fields to `struct proc`:

```c
int pred_burst;
int burst_start;
int cpu_ticks;
int sleep_ticks;
int wclass;
int last_ran_tick;
int wait_ticks;
int priority;
```

## Constants

```c
ALPHA = 50
SCALE = 100
PRED_BURST_SEED = 10
IO_BONUS = 5
IO_THRESHOLD = 60
AGE_WEIGHT = 1
AGE_INTERVAL = 10
AGE_CAP = 500
```

## Burst prediction

```text
pred_burst =
(ALPHA * actual_burst + (SCALE - ALPHA) * pred_burst) / SCALE
```

## Classification

```text
io_ratio =
(sleep_ticks * 100) / (cpu_ticks + sleep_ticks + 1)

io_ratio >= IO_THRESHOLD -> IO_BOUND
otherwise -> CPU_BOUND
```

## Priority

```text
priority =
pred_burst - class_bonus -
(AGE_WEIGHT * (wait_ticks / AGE_INTERVAL))

class_bonus = IO_BONUS for IO_BOUND
class_bonus = 0 for CPU_BOUND

if wait_ticks >= AGE_CAP:
    priority = 0
```

LOWER priority value = HIGHER scheduling preference.

No floating point.

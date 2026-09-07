# xv6 scheduler baseline notes

## Located implementation

- `scheduler()` is in `kernel/proc.c:429` (declared in `kernel/defs.h:95`).
  It is per-CPU, loops forever, scans `proc[0..NPROC)`, acquires each
  `p->lock`, and dispatches each `RUNNABLE` process in array order by changing
  its state to `RUNNING` and calling `swtch()`. It waits with `wfi` when no
  process was found. This is the selection behavior left unchanged in Phase 1.
- `allocproc()` is the static function at `kernel/proc.c:110`. It scans the
  array, acquires each process lock, chooses an `UNUSED` entry, sets it to
  `USED`, initializes its context, and returns with that selected `p->lock`
  still held.
- `sleep_prepare()` is `kernel/proc.c:548`; it records the channel under
  `p->lock`. `sleep()` is `kernel/proc.c:563`; it acquires `p->lock`, changes
  the state to `SLEEPING` if the channel remains set, and calls `sched()`.
- `wakeup()` is `kernel/proc.c:577`; it scans all processes, locks each one,
  clears a matching channel, and changes `SLEEPING` to `RUNNABLE`.
- The requested exit path is named `kexit()` in this source tree, at
  `kernel/proc.c:325`, and is declared in `kernel/defs.h:85`. It acquires
  `wait_lock`, reparents children, wakes the parent, locks the exiting process,
  sets `ZOMBIE`, and enters `sched()`.
- `yield()` is `kernel/proc.c:501` (declared in `kernel/defs.h:102`). It takes
  `p->lock`, changes `RUNNING` to `RUNNABLE`, invokes `sched()`, and releases
  the lock after resumption.

## Locking model actually present

This xv6 version has one spinlock embedded in every `struct proc`, not a
single lock for the process table. `procinit()` in `kernel/proc.c:46`
initializes every `p->lock`; scheduler, allocation, sleep, wakeup, and yield
use those individual locks. `kernel/proc.h:85-90` explicitly requires
`p->lock` for `state`, `chan`, `killed`, `xstate`, and `pid`.

Parent-pointer coordination is separate: `kernel/proc.h:92-93` requires
`wait_lock`, and `kernel/proc.c:20-21` states it must be acquired before any
`p->lock`. PID allocation uses the independent `pid_lock`.

The scheduler holds the selected process's `p->lock` across `swtch()`;
`forkret()` releases it on a process's first entry, and `sched()` requires the
current process lock to be the only held lock before switching back.

## Tick and timer mechanism

`ticks` and `tickslock` are global definitions in `kernel/trap.c:9-10`, with
extern declarations in `kernel/defs.h:142` and `kernel/defs.h:145`.
`trapinit()` initializes `tickslock` at `kernel/trap.c:20-23`.

`devintr()` at `kernel/trap.c:188` recognizes supervisor timer interrupts
(`scause == 0x8000000000000005L`), calls `clockintr()`, and returns 2.
`clockintr()` at `kernel/trap.c:167` increments `ticks` only on CPU 0 while
holding `tickslock`, calls `wakeup(&ticks)`, and programs the next timer with
`w_stimecmp(r_time() + 1000000)` (commented as about one tenth of a second).
Timer result 2 causes preemption through `yield()` in `usertrap()` at lines
84-86 and in `kerneltrap()` at lines 156-158.

`NPROC` is 64 and `NCPU` is 8 in `kernel/param.h:1-2`.

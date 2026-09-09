#!/usr/bin/env python3
"""Install the Phase 5 accounting mechanism on an xv6 vanilla worktree."""
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
def replace(path, old, new):
    p = root / path; text = p.read_text()
    if new in text: return
    if old not in text: raise SystemExit(f"expected text missing in {path}: {old[:48]!r}")
    p.write_text(text.replace(old, new, 1))
replace('kernel/proc.h', '  int pid;              // Process ID\n', '''  int pid;              // Process ID
  // Phase 5 measurement fields; scheduler policy never reads these.
  int eval_creation_tick;
  int eval_first_run_tick;
  int eval_cpu_ticks;
  int eval_wait_ticks;
  int eval_context_switches;
''')
replace('kernel/proc.c', 'static void freeproc(struct proc *p);', '''static void freeproc(struct proc *p);

static int
eval_workload(struct proc *p)
{
  return strncmp(p->name, "cpubound", 16) == 0 || strncmp(p->name, "iobound", 16) == 0 ||
         strncmp(p->name, "mixed", 16) == 0 || strncmp(p->name, "starvation", 16) == 0;
}''')
replace('kernel/proc.c', '  p->state = USED;\n', '''  p->state = USED;
  p->eval_creation_tick = ticks;
  p->eval_first_run_tick = -1;
  p->eval_cpu_ticks = 0;
  p->eval_wait_ticks = 0;
  p->eval_context_switches = 0;
''')
replace('kernel/proc.c', '  p->xstate = status;\n  p->state = ZOMBIE;', '''  p->xstate = status;
  if (eval_workload(p)) {
    int response = p->eval_first_run_tick < 0 ? -1 : p->eval_first_run_tick - p->eval_creation_tick;
    printk("FSSTAT workload=%s pid=%d cpu_ticks=%d wait_ticks=%d response_ticks=%d turnaround_ticks=%d context_switches=%d\\n", p->name, p->pid, p->eval_cpu_ticks, p->eval_wait_ticks, response, ticks - p->eval_creation_tick, p->eval_context_switches);
  }
  p->state = ZOMBIE;''')
replace('kernel/proc.c', '        p->state = RUNNING;\n        c->proc = p;', '''    if (p->eval_first_run_tick < 0)
      p->eval_first_run_tick = ticks;
    p->eval_context_switches++;
        p->state = RUNNING;
        c->proc = p;''')
needle = '''void
yield(void)
{
  struct proc *p = myproc();
  acquire(&p->lock);
  p->state = RUNNABLE;
  sched();
  release(&p->lock);
}
'''
replace('kernel/proc.c', needle, needle + '''
void
eval_tick_update(void)
{
  struct proc *p;
  for (p = proc; p < &proc[NPROC]; p++) {
    acquire(&p->lock);
    if (p->state == RUNNING) p->eval_cpu_ticks++;
    else if (p->state == RUNNABLE) p->eval_wait_ticks++;
    release(&p->lock);
  }
}
''')
replace('kernel/defs.h', 'void            procinit(void);\n', 'void            procinit(void);\nvoid            eval_tick_update(void);\n')
replace('kernel/trap.c', '    ticks++;\n    wakeup(&ticks);', '    ticks++;\n    eval_tick_update();\n    wakeup(&ticks);')

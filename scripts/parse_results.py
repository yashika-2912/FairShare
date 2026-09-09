#!/usr/bin/env python3
"""Parse FSSTAT records emitted by Phase 5 xv6 runs into reproducible CSVs."""
import argparse, csv, re
from collections import defaultdict
from pathlib import Path
FIELDS = ['scheduler', 'workload', 'repetition', 'pid', 'cpu_ticks', 'wait_ticks', 'response_ticks', 'turnaround_ticks', 'context_switches']
PATTERN = re.compile(r'FSSTAT workload=(\w+) pid=(\d+) cpu_ticks=(\d+) wait_ticks=(\d+) response_ticks=(-?\d+) turnaround_ticks=(\d+) context_switches=(\d+)')
def jain(values): return (sum(values) ** 2 / (len(values) * sum(x*x for x in values))) if values and sum(x*x for x in values) else 0.0
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--experiments',default='experiments'); args=ap.parse_args(); root=Path(args.experiments); rows=[]
 for scheduler in ('vanilla','fairshare'):
  for log in sorted((root/scheduler).glob('*.log')):
   parts=log.stem.rsplit('_',1)
   if len(parts)!=2 or not parts[1].isdigit(): continue
   workload,repetition=parts[0],int(parts[1])
   for m in PATTERN.finditer(log.read_text(errors='replace')):
    wk,pid,cpu,wait,response,turnaround,ctx=m.groups(); rows.append(dict(zip(FIELDS,[scheduler,wk,repetition,int(pid),int(cpu),int(wait),int(response),int(turnaround),int(ctx)])))
 rows.sort(key=lambda r:(r['scheduler'],r['workload'],r['repetition'],r['pid']))
 with (root/'results.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
 grouped=defaultdict(list)
 for r in rows: grouped[(r['scheduler'],r['workload'],r['repetition'])].append(r['cpu_ticks'])
 with (root/'fairness.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['scheduler','workload','repetition','participants','jains_fairness_index']); w.writeheader()
  for (s,wk,rep),values in sorted(grouped.items()): w.writerow({'scheduler':s,'workload':wk,'repetition':rep,'participants':len(values),'jains_fairness_index':f'{jain(values):.6f}'})
if __name__=='__main__': main()

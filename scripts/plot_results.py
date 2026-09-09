#!/usr/bin/env python3
"""Generate Phase 5 scheduler comparison charts from parsed CSV data."""
import argparse,csv
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
METRICS=[('wait_ticks','Waiting time (ticks)','waiting_time.png'),('response_ticks','Response time (ticks)','response_time.png'),('turnaround_ticks','Turnaround time (ticks)','turnaround_time.png'),('cpu_ticks','CPU time (ticks)','cpu_time.png'),('context_switches','Context switches','context_switches.png')]
def averages(rows,metric):
 b=defaultdict(list)
 for r in rows:b[(r['workload'],r['scheduler'])].append(float(r[metric]))
 ws=sorted({r['workload'] for r in rows}); return ws,[[sum(b[(w,s)])/len(b[(w,s)]) if b[(w,s)] else 0 for w in ws] for s in ('vanilla','fairshare')]
def chart(ws,series,label,out):
 x=range(len(ws)); fig,ax=plt.subplots(figsize=(8,4.5)); ax.bar([i-.19 for i in x],series[0],.38,label='Vanilla xv6'); ax.bar([i+.19 for i in x],series[1],.38,label='FairShare xv6'); ax.set_xticks(list(x),ws); ax.set_ylabel(label); ax.legend(); ax.grid(axis='y',alpha=.25); fig.tight_layout(); fig.savefig(out,dpi=160); plt.close(fig)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--experiments',default='experiments');args=ap.parse_args();root=Path(args.experiments);out=root/'plots';out.mkdir(parents=True,exist_ok=True)
 with (root/'results.csv').open() as f:rows=list(csv.DictReader(f))
 for m,label,name in METRICS: chart(*averages(rows,m),label,out/name)
 with (root/'fairness.csv').open() as f: fair=list(csv.DictReader(f))
 b=defaultdict(list)
 for r in fair:b[(r['workload'],r['scheduler'])].append(float(r['jains_fairness_index']))
 ws=sorted({r['workload'] for r in fair}); series=[[sum(b[(w,s)])/len(b[(w,s)]) if b[(w,s)] else 0 for w in ws] for s in ('vanilla','fairshare')];chart(ws,series,"Jain's Fairness Index",out/'jains_fairness_index.png')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Run matched Phase 5 xv6 trials in disposable git worktrees."""
import argparse, shutil, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
WORKLOADS = ('cpubound', 'iobound', 'mixed', 'starvation')
def run(cmd, cwd, **kw): return subprocess.run(cmd, cwd=cwd, check=True, **kw)
def prepare(root, name, revision, vanilla):
    path = Path('/tmp') / f'fairshare-phase5-{name}'
    if path.exists(): shutil.rmtree(path)
    run(['git', 'worktree', 'prune'], root)
    run(['git','worktree','add','--detach',str(path),revision], root)
    if vanilla:
        for source in WORKLOADS: shutil.copy2(root/'user'/f'{source}.c', path/'user'/f'{source}.c')
        makefile=(path/'Makefile'); text=makefile.read_text()
        marker = "\t$U/_sync\\\n"
        additions = ''.join(f"\t$U/_{w}\\\n" for w in WORKLOADS)
        if '$U/_cpubound' not in text: makefile.write_text(text.replace(marker, marker+additions))
        run([sys.executable, str(root/'scripts/install_vanilla_instrumentation.py'), str(path)], root)
    return path
def trial(tree, workload, log):
    run(['make','clean'],tree,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    run(['make','CPUS=1','kernel/kernel','fs.img'],tree,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    command=['qemu-system-riscv64','-machine','virt','-bios','none','-kernel','kernel/kernel','-m','128M','-smp','1','-nographic','-global','virtio-mmio.force-legacy=false','-drive','file=fs.img,if=none,format=raw,id=x0','-device','virtio-blk-device,drive=x0,bus=virtio-mmio-bus.0']
    with log.open('wb') as out:
        p=subprocess.Popen(command,cwd=tree,stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT)
        time.sleep(1); p.stdin.write((workload+'\n').encode()); p.stdin.flush()
        deadline=time.time()+120
        while time.time()<deadline:
            time.sleep(.5); out.flush()
            if log.exists() and f'{workload}: done'.encode() in log.read_bytes(): break
            if workload == 'starvation' and log.exists() and (b'starvation: PASS' in log.read_bytes() or b'starvation: hog failed' in log.read_bytes()): break
        else:
            p.stdin.write(b'\x01x'); p.stdin.flush(); p.wait(timeout=10); raise RuntimeError(f'{workload} timed out')
        p.stdin.write(b'\x01x'); p.stdin.flush(); p.wait(timeout=10)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repetitions',type=int,default=3);args=ap.parse_args()
    trees=[]
    try:
        trees=[('vanilla',prepare(ROOT,'vanilla','vanilla-baseline',True)),('fairshare',prepare(ROOT,'fairshare','HEAD',False))]
        for name,tree in trees:
            out=ROOT/'experiments'/name;out.mkdir(parents=True,exist_ok=True)
            for workload in WORKLOADS:
                for rep in range(1,args.repetitions+1): trial(tree,workload,out/f'{workload}_{rep}.log')
        run([sys.executable,'scripts/parse_results.py'],ROOT);run([sys.executable,'scripts/plot_results.py'],ROOT)
    finally:
        for _,tree in trees:
            subprocess.run(['git','worktree','remove','--force',str(tree)],cwd=ROOT)
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Fail-closed verifier for one P2q task x Profile cell."""
from __future__ import annotations
import argparse, ast, hashlib, json, statistics, subprocess
from pathlib import Path

TASKS={
"keyed-closest-negative":{"package":"perf_keyed_closest_negative_p2q","data":((0,3),(0,-1),(1,9),(1,-4)),"queries":(0,1,2,9),"expected":[-1,-4,None,None]},
"keyed-distinct-quartic-sum":{"package":"perf_keyed_distinct_quartic_sum_p2q","data":((0,-1),(0,-1),(0,2),(1,3)),"queries":(0,1,2,9),"expected":[17,81,0,0]},
"rotate-mix32":{"package":"perf_rotate_mix32_p2q","data":(3,7,11,3,101),"queries":(-3,0,8,99),"expected":[83,80,77,5]},
}
IMPL=("api.py","observer.py","shared.py","target.py"); FROZEN=(".modus-task.json","benchmark.py","instruction.md","tests/test_public.py")
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _run(c,cwd,t=300):
 try:
  d=subprocess.run(c,cwd=cwd,capture_output=True,text=True,timeout=t);return {"returncode":d.returncode,"stdout":d.stdout[-4000:],"stderr":d.stderr[-4000:],"timed_out":False}
 except subprocess.TimeoutExpired:return {"returncode":None,"stdout":"","stderr":"","timed_out":True}
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--workspace",type=Path,required=True);p.add_argument("--seed",type=Path,required=True);p.add_argument("--task",choices=tuple(TASKS),required=True);p.add_argument("--profile",choices=("neutral","p000v2","e1v3"),required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--python",required=True);a=p.parse_args(argv)
 w=a.workspace.resolve();s=a.seed.resolve();spec=TASKS[a.task];pkg=spec["package"]
 public=_run([a.python,"-m","unittest","discover","-s","tests","-v"],w,120)
 program=f"from {pkg}.api import execute\ndata={spec['data']!r}\nq={spec['queries']!r}\ne={spec['expected']!r}\nr=execute(data,(q,))[0]\nassert r==e,(r,e)\nprint('hidden-ok')\n"
 hidden=_run([a.python,"-c",program],w,120);correct=public["returncode"]==hidden["returncode"]==0 and "hidden-ok" in hidden["stdout"]
 custody=all((w/r).is_file() and _sha(w/r)==_sha(s/r) for r in FROZEN)
 changed=[f"{pkg}/{n}" for n in IMPL if not (w/pkg/n).is_file() or _sha(w/pkg/n)!=_sha(s/pkg/n)]
 wanted={"neutral":None,"p000v2":[f"{pkg}/target.py"],"e1v3":[f"{pkg}/observer.py",f"{pkg}/shared.py",f"{pkg}/target.py"]}[a.profile]
 topology=True if wanted is None else changed==wanted
 mechanism=None
 if a.profile=="e1v3":
  mprog=f"from {pkg} import observer,target\ndata={spec['data']!r}\nq={spec['queries']!r}\ne={spec['expected']!r}\np=observer.prepare_input(data)\nassert p is not data\nassert target.answer(p,q)==e\nprint('mechanism-ok')\n"
  mechanism=_run([a.python,"-c",mprog],w,120);mechanism_ok=mechanism["returncode"]==0 and "mechanism-ok" in mechanism["stdout"]
 else: mechanism_ok=True
 samples=[]; failed=None
 for _ in range(15):
  d=_run([a.python,"benchmark.py"],w,300)
  if d["returncode"]!=0:failed=d;break
  try:
   text=d["stdout"].strip()
   try:v=json.loads(text)
   except json.JSONDecodeError:v=ast.literal_eval(text.splitlines()[-1])
   samples.append(float(v["seconds"]))
  except Exception:failed=d;break
 if len(samples)==15:
  steady=sorted(samples)[:7];sec=statistics.median(steady);mad=statistics.median(abs(x-sec) for x in steady)/sec if sec else 0.0;bench=True
 else:sec=mad=None;bench=False
 checks={"custody":custody,"correctness":correct,"topology":topology,"semantic_mechanism":mechanism_ok,"benchmark":bench}
 digest=hashlib.sha256();
 for path in sorted((w/pkg).glob("*.py")):digest.update(path.name.encode()+b"\0"+path.read_bytes()+b"\0")
 report={"schema":"modus-performance-p2q-cell-verification-v1","task":a.task,"profile":a.profile,"checks":checks,"passed":all(checks.values()),"implementation_digest":digest.hexdigest(),"changed_implementation_paths":changed,"correctness":{"public":public,"hidden":hidden},"semantic_mechanism":mechanism,"benchmark":{"success":bench,"rounds":len(samples),"all_seconds":samples,"steady_seconds":sec,"steady_relative_mad":mad,"failed_run":failed}}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"task":a.task,"profile":a.profile,"passed":report["passed"],"seconds":sec},sort_keys=True));return 0 if report["passed"] else 2
if __name__=="__main__":raise SystemExit(main())

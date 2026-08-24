#!/usr/bin/env python3
"""Score the P2n nine-cell Profile preference matrix and Agent route."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent;SOURCE_ROOT=SCRIPT_DIR.parent/"src"
for c in (SCRIPT_DIR,SOURCE_ROOT):
 if str(c) not in sys.path:sys.path.insert(0,str(c))
from acrouter_repro.qualification_economics import evaluate_qualification_economics
from score_modus_long_horizon_p2a_pipeline import _sha256,_wave_usage
TASKS=("keyed-distinct-min","keyed-distinct-cube-sum","affine-checksum");PROFILES=("neutral","p000v2","e1v3")
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--run-root",type=Path,required=True);p.add_argument("--protocol",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args(argv)
 root=a.run_root.resolve();protocol=json.loads(a.protocol.read_text());repo=a.protocol.resolve().parents[1];rows=[]
 for cell in protocol["cells"]:
  cr=root/"cells"/cell["id"];vp=cr/"verification.json";v=json.loads(vp.read_text());ok,tokens=_wave_usage(cr/"output/wave-result.json")
  rows.append({**cell,"valid":v["passed"] and ok,"seconds":v["benchmark"]["steady_seconds"],"relative_mad":v["benchmark"]["steady_relative_mad"],"worker_tokens":tokens,"implementation_digest":v["implementation_digest"],"verification_sha256":_sha256(vp)})
 by={(r["task"],r["profile"]):r for r in rows};task_results={};selected={}
 for task in TASKS:
  neutral=by[(task,"neutral")];candidates={}
  for profile in PROFILES:
   r=by[(task,profile)];ratio=r["seconds"]/neutral["seconds"] if neutral["seconds"] else None;saving=0.0 if profile=="neutral" else 1-r["worker_tokens"]/neutral["worker_tokens"]
   gates={"valid":r["valid"],"performance":ratio is not None and ratio<=1.25,"noise":r["relative_mad"]<=0.10}
   if profile!="neutral":gates["token_saving"]=saving>=0.15
   candidates[profile]={"performance_ratio_to_neutral":ratio,"token_saving_fraction_vs_neutral":saving,"gates":gates,"eligible":all(gates.values())}
  eligible=[x for x in PROFILES if candidates[x]["eligible"]];choice=min(eligible,key=lambda x:by[(task,x)]["worker_tokens"],default=None);selected[task]=choice
  task_results[task]={"candidates":candidates,"selected_profile":choice,"expected_preference":protocol["tasks"][task]["expected_preference"]}
 router=json.loads((repo/protocol["parent_router"]["score_path"]).read_text());agent=router["parsed"]["actions_by_task"];matches={t:agent[t]==selected[t] for t in TASKS}
 fixed=sum(by[(t,"neutral")]["worker_tokens"] for t in TASKS);route_tokens=sum(by[(t,selected[t])]["worker_tokens"] for t in TASKS if selected[t]);all_selected=len(selected)==3 and all(selected.values());candidate=route_tokens
 acquisition=protocol["parent_router"]["router_tokens"]+sum(r["worker_tokens"] for r in rows)
 saving=1-candidate/fixed if all_selected else 0.0;qualified=all_selected and all(r["valid"] for r in rows)
 econ=evaluate_qualification_economics(acquisition_tokens=acquisition,baseline_deployment_tokens=fixed,candidate_deployment_tokens=candidate,expected_deployments=8,correctness_passed=qualified,performance_passed=qualified,evidence_stable=qualified,minimum_saving_fraction=0.15)
 distinct=len(set(selected.values())) if all_selected else 0
 report={"schema":"modus-performance-p2n-matrix-score-v1","status":"pass" if all(r["valid"] for r in rows) else "fail","rows":rows,"tasks":task_results,"selected_route":selected,"distinct_selected_profiles":distinct,"task_dependent_preference_observed":distinct>=2,"agent_route":agent,"agent_matches":matches,"agent_match_count":sum(matches.values()),"deployment":{"fixed_neutral_tokens":fixed,"selected_route_tokens":candidate,"saving_fraction":saving},"acquisition_tokens":acquisition,"economics":econ,"decision":"promote_task_dependent_router" if qualified and distinct>=2 and econ["decision"]=="promote" else "stop_or_continue_evidence","claim_boundary":"one task per type is preliminary task-dependent preference evidence"}
 a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"status":report["status"],"selected_route":selected,"distinct_profiles":distinct,"agent_match_count":report["agent_match_count"],"saving_fraction":saving,"break_even":econ["break_even_deployments"],"net_at_8":econ["net_tokens_at_expected_deployments"],"decision":report["decision"]},sort_keys=True));return 0 if report["status"]=="pass" else 2
if __name__=="__main__":raise SystemExit(main())

#!/usr/bin/env python3
"""Validate one custody-confined P2p Router decision."""
import argparse,json
from pathlib import Path
SCHEMA="modus-performance-p2p-router-decision-v1"
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--run-root",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args(argv);root=a.run_root.resolve();wave=json.loads((root/"output/wave-result.json").read_text());cell=wave["cells"][0];msg=root/"output"/cell["cell"]/"last-message.txt";value=error=None
 try:
  value=json.loads(msg.read_text());assert set(value)=={"schema","action","reason"};assert value["schema"]==SCHEMA;assert value["action"] in {"neutral","p000v2","e1v3"};assert isinstance(value["reason"],str) and value["reason"].strip()
 except Exception as exc:error=str(exc);value=None
 u=cell.get("usage");tokens=u["input_tokens"]+u["output_tokens"] if isinstance(u,dict) else None;valid=value is not None and tokens is not None and wave["status"]=="pass";report={"schema":"modus-performance-p2p-router-validation-v1","status":"pass" if valid else "fail","decision":value,"parse_error":error,"router_tokens":tokens,"worker_triplet_authorized":valid,"deployment_authorized":False};a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(report,sort_keys=True));return 0 if valid else 2
if __name__=="__main__":raise SystemExit(main())

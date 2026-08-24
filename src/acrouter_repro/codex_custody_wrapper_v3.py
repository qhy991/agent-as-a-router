#!/usr/bin/env python3
"""Launch Codex from the allowed workspace with source-root-safe imports."""
from __future__ import annotations
import os,sys
from pathlib import Path
SOURCE_ROOT=Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:sys.path.insert(0,str(SOURCE_ROOT))
from acrouter_repro.codex_custody_wrapper import build_profile
def main():
 args=sys.argv[1:]
 try: workspace=Path(args[args.index("-C")+1]).resolve()
 except (ValueError,IndexError) as error: raise SystemExit("custody wrapper requires Codex -C workspace") from error
 roots=[Path(v) for v in os.environ.get("MODUS_CUSTODY_DENY_ROOTS","").split(os.pathsep) if v]
 if not roots:raise SystemExit("MODUS_CUSTODY_DENY_ROOTS is empty")
 profile=build_profile(workspace,roots);real=os.environ.get("MODUS_REAL_CODEX","/Users/haiyan-infiniai/.local/bin/codex");os.chdir(workspace);os.execv("/usr/bin/sandbox-exec",["sandbox-exec","-p",profile,real,*args])
if __name__=="__main__":main()

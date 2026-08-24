#!/usr/bin/env python3
"""Resolve a persisted Modus qualification request without a Router model call."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.modus_qualification_request import resolve_qualification_request  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--candidate-view", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = resolve_qualification_request(
        json.loads(args.request.read_text()), json.loads(args.candidate_view.read_text())
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "request_id": result["request_id"], "worker_dispatch": result["worker_dispatch"]}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())

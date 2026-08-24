#!/usr/bin/env python3
"""Build one manager dispatch plan from a scored evidence-gated Agent response."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.modus_dispatch_plan import build_dispatch_plan  # noqa: E402
from acrouter_repro.modus_route_cache import sha256_value  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--candidate-view", type=Path, required=True)
    parser.add_argument("--agent-score", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    protocol = json.loads(args.protocol.read_text())
    view = json.loads(args.candidate_view.read_text())
    score = json.loads(args.agent_score.read_text())
    if score.get("status") != "pass" or not isinstance(score.get("response"), dict):
        raise ValueError("Agent score is not a valid passed response")
    plan = build_dispatch_plan(
        response=score["response"],
        contract=protocol["response_contract"],
        candidate_view=view,
        response_sha256=sha256_value(score["response"]),
        candidate_view_sha256=hashlib.sha256(args.candidate_view.read_bytes()).hexdigest(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": plan["status"],
        "dispatches": len(plan["worker_dispatches"]),
        "qualification_requests": len(plan["qualification_requests"]),
        "neutral_fallbacks": plan["neutral_fallbacks"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

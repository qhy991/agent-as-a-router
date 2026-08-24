#!/usr/bin/env python3
"""Score one qualified Worker dispatch while preserving an abstained request."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.run_root.resolve()
    repo = args.protocol.resolve().parents[1]
    protocol = json.loads(args.protocol.read_text())
    plan = json.loads((repo / protocol["dispatch_plan"]["path"]).read_text())
    request = json.loads((repo / protocol["qualification_request"]["path"]).read_text())
    wave = json.loads((root / "qualified-output/wave-result.json").read_text())
    verification = json.loads((root / "qualified-verification.json").read_text())
    cell = wave["cells"][0]
    usage = cell.get("usage")
    request_matches = plan["qualification_requests"] == [request]
    unqualified_side_effects = any((
        (root / "unqualified-workspace").exists(),
        (root / "unqualified-manifest.json").exists(),
        (root / "unqualified-output").exists(),
    ))
    checks = {
        "source_plan_partial": plan["status"] == "partial_pending_qualification" and not plan["complete"],
        "one_qualified_dispatch": len(plan["worker_dispatches"]) == 1,
        "request_persisted_exactly": request_matches,
        "qualified_worker_valid": wave["status"] == "pass" and cell["valid_execution"],
        "qualified_worker_verified": verification["passed"],
        "unqualified_worker_calls_zero": not unqualified_side_effects,
        "neutral_fallbacks_zero": plan["neutral_fallbacks"] == 0,
    }
    report = {
        "schema": "modus-partial-lifecycle-p2f-result-v1",
        "status": "pass" if all(checks.values()) else "fail",
        "lifecycle_status": "partial_pending_qualification",
        "complete": False,
        "checks": checks,
        "qualified_dispatch": plan["worker_dispatches"][0],
        "qualified_worker": {
            "verification": verification,
            "usage": usage,
            "total_tokens": usage["input_tokens"] + usage["output_tokens"] if usage else None,
        },
        "qualification_request": request,
        "unqualified_worker_calls": 0 if not unqualified_side_effects else None,
        "neutral_fallbacks": plan["neutral_fallbacks"],
        "source_hashes": {
            "dispatch_plan_sha256": hashlib.sha256((repo / protocol["dispatch_plan"]["path"]).read_bytes()).hexdigest(),
            "qualification_request_sha256": hashlib.sha256((repo / protocol["qualification_request"]["path"]).read_bytes()).hexdigest(),
        },
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"], "lifecycle_status": report["lifecycle_status"],
        "qualified_worker_tokens": report["qualified_worker"]["total_tokens"],
        "unqualified_worker_calls": report["unqualified_worker_calls"],
        "request_id": request["request_id"],
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

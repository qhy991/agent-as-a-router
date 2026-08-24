#!/usr/bin/env python3
"""Close the P2f partial lifecycle after accepted offline qualification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.run_root.resolve(); repo = args.protocol.resolve().parents[1]
    protocol = json.loads(args.protocol.read_text())
    previous = json.loads((repo / protocol["previous_lifecycle"]).read_text())
    resolution = json.loads((repo / protocol["qualification_resolution"]).read_text())
    wave = json.loads((root / "qualified-output/wave-result.json").read_text())
    verification = json.loads((root / "qualified-verification.json").read_text())
    cell = wave["cells"][0]; usage = cell.get("usage")
    checks = {
        "previous_partial": previous["lifecycle_status"] == "partial_pending_qualification" and not previous["complete"],
        "request_resolution_accepted": resolution["status"] == "accepted",
        "request_identity_preserved": resolution["request_id"] == previous["qualification_request"]["request_id"],
        "continuation_worker_valid": wave["status"] == "pass" and cell["valid_execution"],
        "continuation_worker_verified": verification["passed"],
        "neutral_fallbacks_zero": previous["neutral_fallbacks"] == resolution["neutral_fallbacks"] == 0,
    }
    second_tokens = usage["input_tokens"] + usage["output_tokens"] if usage else None
    report = {
        "schema": "modus-completed-lifecycle-p2g-result-v1",
        "status": "pass" if all(checks.values()) else "fail",
        "lifecycle_status": "complete" if all(checks.values()) else "partial_pending_qualification",
        "complete": all(checks.values()),
        "checks": checks,
        "workers": {
            "initial_qualified_worker_tokens": previous["qualified_worker"]["total_tokens"],
            "continuation_worker_tokens": second_tokens,
            "total_worker_tokens": previous["qualified_worker"]["total_tokens"] + second_tokens if second_tokens else None,
        },
        "resolved_request": resolution,
        "continuation_dispatch": resolution["worker_dispatch"],
        "continuation_verification": verification,
        "pending_qualification_requests": 0 if all(checks.values()) else 1,
        "neutral_fallbacks": 0,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "lifecycle_status": report["lifecycle_status"], "complete": report["complete"], "total_worker_tokens": report["workers"]["total_worker_tokens"]}, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__": raise SystemExit(main())

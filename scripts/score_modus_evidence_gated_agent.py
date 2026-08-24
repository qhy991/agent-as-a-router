#!/usr/bin/env python3
"""Validate live Agent dispatch and abstention under qualified route contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.codex_spark_shadow import (  # noqa: E402
    _validate_profile_mechanism_contract,
    validate_profile_mechanism_response,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.run_root.resolve()
    protocol = json.loads(args.protocol.read_text())
    wave = json.loads((root / "output/wave-result.json").read_text())
    by_cell = {cell["cell"]: cell for cell in wave["cells"]}
    rows = []
    for case in protocol["cases"]:
        contract = _validate_profile_mechanism_contract(case["response_contract"])
        cell = by_cell[case["cell"]]
        message = root / "output" / case["cell"] / "last-message.txt"
        response, error = None, None
        try:
            response = json.loads(message.read_text())
            error = validate_profile_mechanism_response(response, contract)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as caught:
            error = str(caught)
        decisions = [route.get("decision") for route in response.get("routes", [])] if isinstance(response, dict) else []
        expected = (
            decisions == ["dispatch", "dispatch"]
            if case["expected"] == "dispatch"
            else decisions == ["abstain", "abstain"]
        )
        passed = cell["valid_execution"] and error is None and expected
        usage = cell.get("usage")
        rows.append({
            "case": case["id"], "cell": case["cell"], "expected": case["expected"],
            "valid_execution": cell["valid_execution"], "response": response,
            "validation_error": error, "expected_behavior_passed": expected,
            "passed": passed, "usage": usage,
            "total_tokens": usage["input_tokens"] + usage["output_tokens"] if usage else None,
        })
    report = {
        "schema": "modus-evidence-gated-agent-live-result-v1",
        "cases": rows,
        "automatic_redispatches": wave.get("automatic_redispatches"),
        "status": "pass" if all(row["passed"] for row in rows) else "fail",
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "cases": {row["case"]: row["response"] for row in rows},
        "tokens": {row["case"]: row["total_tokens"] for row in rows},
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate one live Agent response against the derived P2e candidate view."""

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
    contract = _validate_profile_mechanism_contract(protocol["response_contract"])
    wave = json.loads((root / "output/wave-result.json").read_text())
    cell = wave["cells"][0]
    message = root / "output/p2e-agent/last-message.txt"
    response, error = None, None
    try:
        response = json.loads(message.read_text())
        error = validate_profile_mechanism_response(response, contract)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as caught:
        error = str(caught)
    expected = ["dispatch", "abstain"]
    observed = [route.get("decision") for route in response.get("routes", [])] if isinstance(response, dict) else []
    passed = cell["valid_execution"] and error is None and observed == expected
    usage = cell.get("usage")
    report = {
        "schema": "modus-p2e-autonomous-evidence-gated-agent-result-v1",
        "status": "pass" if passed else "fail",
        "valid_execution": cell["valid_execution"],
        "response": response,
        "validation_error": error,
        "expected_decisions": expected,
        "observed_decisions": observed,
        "workers_called": 0,
        "usage": usage,
        "total_tokens": usage["input_tokens"] + usage["output_tokens"] if usage else None,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Score the development-only E1-v2 mechanism calibration."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


PERFORMANCE_RATIO_MAXIMUM = 1.25
NOISE_RELATIVE_MAD_MAXIMUM = 0.10


def _usage_tokens(usage: dict) -> int | None:
    if not isinstance(usage, dict):
        return None
    if not all(isinstance(usage.get(key), int) for key in ("input_tokens", "output_tokens")):
        return None
    return usage["input_tokens"] + usage["output_tokens"]


def _aggregate(entries: list[dict]) -> dict:
    seconds = [
        entry["benchmark"]["steady_seconds"]
        for entry in entries if entry.get("benchmark") and entry["benchmark"].get("success")
    ]
    tokens = [_usage_tokens(entry.get("usage")) for entry in entries]
    mads = [
        entry["benchmark"].get("steady_relative_median_absolute_deviation")
        for entry in entries if entry.get("benchmark")
    ]
    complete = (
        len(seconds) == len(entries)
        and all(value is not None for value in tokens)
        and all(value is not None for value in mads)
    )
    return {
        "correctness_passed": all(entry["correct"] for entry in entries),
        "topology_fidelity_passed": all(
            entry["topology_fidelity_passed"] for entry in entries
        ),
        "semantic_mechanism_passed": all(
            entry["semantic_mechanism_passed"] for entry in entries
        ),
        "benchmark_and_usage_complete": complete,
        "median_seconds": statistics.median(seconds) if complete else None,
        "median_total_tokens": statistics.median(tokens) if complete else None,
        "maximum_steady_relative_mad": max(mads) if complete else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args(argv)

    protocol = json.loads(options.protocol.read_text(encoding="utf-8"))
    verification = json.loads(
        (options.run_root.resolve() / "manager-verification.json").read_text()
    )
    by_action = {
        action: [cell for cell in verification["cells"] if cell["action"] == action]
        for action in protocol["matrix"]["actions"]
    }
    actions = {action: _aggregate(entries) for action, entries in by_action.items()}
    complete = verification.get("status") == "pass" and all(
        action["benchmark_and_usage_complete"] for action in actions.values()
    )
    fastest = min(action["median_seconds"] for action in actions.values()) if complete else None
    for action in actions.values():
        ratio = action["median_seconds"] / fastest if complete else None
        action["performance_ratio_to_fastest"] = ratio
        action["performance_gate_passed"] = bool(
            complete and ratio <= PERFORMANCE_RATIO_MAXIMUM
        )
        action["noise_gate_passed"] = bool(
            complete
            and action["maximum_steady_relative_mad"] <= NOISE_RELATIVE_MAD_MAXIMUM
        )

    candidate = actions["e1v2"]
    calibration_passed = all((
        complete,
        candidate["correctness_passed"],
        candidate["topology_fidelity_passed"],
        candidate["semantic_mechanism_passed"],
        candidate["performance_gate_passed"],
        candidate["noise_gate_passed"],
    ))
    parent = protocol["parent_outcome"]
    candidate_speedup_over_canonical = (
        parent["canonical_p100_median_seconds"] / candidate["median_seconds"]
        if complete else None
    )
    candidate_saving_vs_neutral = (
        1.0 - candidate["median_total_tokens"] / actions["neutral"]["median_total_tokens"]
        if complete else None
    )
    acquisition = sum(
        _usage_tokens(cell["usage"]) for cell in verification["cells"]
        if _usage_tokens(cell.get("usage")) is not None
    )
    report = {
        "schema": "modus-reachability-p1e-e1v2-calibration-score-v1",
        "status": "pass" if complete else "fail",
        "development_only": True,
        "actions": actions,
        "candidate": {
            "id": "e1-v2",
            "calibration_passed": calibration_passed,
            "speedup_over_canonical_p100": candidate_speedup_over_canonical,
            "token_saving_fraction_vs_fresh_neutral": candidate_saving_vs_neutral,
        },
        "acquisition_tokens": acquisition,
        "decision": (
            "authorize_new_holdout_design" if calibration_passed
            else "retain_unqualified_and_stop"
        ),
        "claim_boundary": "Observed-task development calibration only; no Router outcome or deployment economics claim.",
    }
    options.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "calibration_passed": calibration_passed,
        "candidate_ratio": candidate["performance_ratio_to_fastest"],
        "candidate_speedup_over_canonical_p100": candidate_speedup_over_canonical,
        "candidate_token_saving_vs_neutral": candidate_saving_vs_neutral,
        "acquisition_tokens": acquisition,
        "decision": report["decision"],
    }, sort_keys=True))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())

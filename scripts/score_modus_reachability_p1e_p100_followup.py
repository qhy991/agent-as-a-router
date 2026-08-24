#!/usr/bin/env python3
"""Score the outcome-authorized P100 follow-up and final P1e route."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.qualification_economics import (  # noqa: E402
    evaluate_qualification_economics,
)


PERFORMANCE_RATIO_MAXIMUM = 1.25
P100_TOKEN_ADVANTAGE_MINIMUM = 0.05
ROUTER_SAVING_MINIMUM = 0.15


def _usage_tokens(usage: dict) -> int | None:
    if not isinstance(usage, dict):
        return None
    if not all(isinstance(usage.get(key), int) for key in ("input_tokens", "output_tokens")):
        return None
    return usage["input_tokens"] + usage["output_tokens"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args(argv)

    protocol = json.loads(options.protocol.read_text(encoding="utf-8"))
    repo = options.protocol.resolve().parents[1]
    parent_score = json.loads((repo / protocol["parent_stage"]["score_path"]).read_text())
    verification = json.loads(
        (options.run_root.resolve() / "manager-verification.json").read_text()
    )
    task_name = next(iter(protocol["tasks"]))
    entries = [cell for cell in verification["cells"] if cell["task"] == task_name]
    usage_tokens = [_usage_tokens(cell["usage"]) for cell in entries]
    benchmark_seconds = [
        cell["benchmark"]["steady_seconds"]
        for cell in entries if cell.get("benchmark") and cell["benchmark"].get("success")
    ]
    complete = (
        verification.get("status") == "pass"
        and len(entries) == protocol["matrix"]["cells"]
        and len(benchmark_seconds) == len(entries)
        and all(value is not None for value in usage_tokens)
    )

    parent_task = parent_score["tasks"][task_name]
    neutral = parent_task["actions"]["neutral"]
    p100_seconds = statistics.median(benchmark_seconds) if complete else None
    p100_tokens = statistics.median(usage_tokens) if complete else None
    fastest = min(neutral["median_seconds"], p100_seconds) if complete else None
    p100_ratio = p100_seconds / fastest if complete else None
    p100_eligible = bool(
        complete
        and p100_ratio <= PERFORMANCE_RATIO_MAXIMUM
        and all(cell["correct"] and cell["topology_fidelity_passed"] for cell in entries)
    )
    p100_saving = (
        1.0 - p100_tokens / neutral["median_total_tokens"] if complete else None
    )
    select_p100 = bool(
        p100_eligible
        and p100_saving is not None
        and p100_saving >= P100_TOKEN_ADVANTAGE_MINIMUM
    )
    x02_action = "p100" if select_p100 else "neutral"
    x02_tokens = p100_tokens if select_p100 else neutral["median_total_tokens"]

    x01 = parent_score["tasks"]["reachability-x01"]
    x01_action = x01["oracle_action"]
    x01_tokens = x01["actions"][x01_action]["median_total_tokens"]
    baseline_tokens = parent_score["fixed_total_median_tokens"]["neutral"]
    routed_tokens = x01_tokens + x02_tokens if complete else None
    followup_acquisition = sum(usage_tokens) if complete else None
    total_acquisition = (
        protocol["parent_stage"]["acquisition_tokens"] + followup_acquisition
        if complete else None
    )
    routed_saving = (
        1.0 - routed_tokens / baseline_tokens if routed_tokens is not None else None
    )
    economics = None
    if complete:
        economics = evaluate_qualification_economics(
            acquisition_tokens=int(round(total_acquisition)),
            baseline_deployment_tokens=int(round(baseline_tokens)),
            candidate_deployment_tokens=int(round(routed_tokens)),
            expected_deployments=protocol["expected_future_deployments"],
            correctness_passed=True,
            performance_passed=True,
            evidence_stable=True,
            minimum_saving_fraction=ROUTER_SAVING_MINIMUM,
        )

    report = {
        "schema": "modus-reachability-p1e-p100-followup-score-v1",
        "status": "pass" if complete else "fail",
        "p100": {
            "correctness_passed": all(cell["correct"] for cell in entries),
            "topology_fidelity_passed": all(
                cell["topology_fidelity_passed"] for cell in entries
            ),
            "usage_complete": all(value is not None for value in usage_tokens),
            "median_seconds": p100_seconds,
            "median_total_tokens": p100_tokens,
            "performance_ratio_to_fastest": p100_ratio,
            "performance_gate_passed": p100_eligible,
            "token_saving_fraction_vs_neutral": p100_saving,
            "selected_for_x02": select_p100,
        },
        "final_route": {
            "actions_by_task": {
                "reachability-x01": x01_action,
                "reachability-x02": x02_action,
            },
            "best_fixed_action": "neutral",
            "best_fixed_median_tokens": baseline_tokens,
            "routed_median_tokens": routed_tokens,
            "saving_fraction_vs_best_fixed": routed_saving,
        },
        "acquisition": {
            "stage1_tokens": protocol["parent_stage"]["acquisition_tokens"],
            "p100_followup_tokens": followup_acquisition,
            "total_tokens": total_acquisition,
        },
        "economics": economics,
    }
    options.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "p100_eligible": p100_eligible,
        "p100_selected": select_p100,
        "final_route": report["final_route"]["actions_by_task"],
        "saving_fraction": routed_saving,
        "break_even": economics["break_even_deployments"] if economics else None,
        "decision_at_expected_deployments": economics["decision"] if economics else None,
    }, sort_keys=True))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())

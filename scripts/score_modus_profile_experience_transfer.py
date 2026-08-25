#!/usr/bin/env python3
"""Score formal Profile experience transfer quality and marginal economics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
for candidate in (SCRIPT_DIR, SOURCE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from acrouter_repro.qualification_economics import (  # noqa: E402
    evaluate_qualification_economics,
)
from score_modus_long_horizon_p2a_pipeline import _sha256, _wave_usage  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--router-score", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.run_root.resolve()
    protocol = json.loads(args.protocol.read_text())
    router = json.loads(args.router_score.read_text())
    execution = json.loads((root / "execution-summary.json").read_text())
    rows = []
    for cell in execution["cells"]:
        cell_root = root / "cells" / cell["id"]
        verification_path = cell_root / "verification.json"
        verification = json.loads(verification_path.read_text())
        usage_ok, tokens = _wave_usage(cell_root / "output/wave-result.json")
        rows.append({
            **cell,
            "valid": verification["passed"] and usage_ok,
            "seconds": verification["benchmark"]["steady_seconds"],
            "relative_mad": verification["benchmark"]["steady_relative_mad"],
            "worker_tokens": tokens,
            "implementation_digest": verification["implementation_digest"],
            "verification_sha256": _sha256(verification_path),
        })
    by_id = {row["id"]: row for row in rows}
    route_by_task = {
        row["task_id"]: row for row in router["parsed"]["routes"]
    }
    baseline_strategy = protocol["execution"]["fixed_baseline_strategy"]
    task_results = {}
    selected_route = {}
    baseline_tokens = 0
    selected_tokens = 0
    for task_id in protocol["router"]["tasks"]:
        route = route_by_task[task_id]
        selected_strategy = (
            baseline_strategy if route["decision"] == "abstain"
            else route["strategy"]
        )
        selected_route[task_id] = selected_strategy
        baseline = by_id[f"{task_id}--reference"]
        selected = (
            baseline if selected_strategy == baseline_strategy
            else by_id[f"{task_id}--selected"]
        )
        ratio = (
            selected["seconds"] / baseline["seconds"]
            if baseline["seconds"] else None
        )
        gates = {
            "baseline_valid": baseline["valid"],
            "selected_valid": selected["valid"],
            "performance": ratio is not None and ratio <= protocol["scoring"]["maximum_performance_ratio"],
            "baseline_noise": baseline["relative_mad"] <= protocol["scoring"]["maximum_relative_mad"],
            "selected_noise": selected["relative_mad"] <= protocol["scoring"]["maximum_relative_mad"],
        }
        expected = protocol["tasks"][task_id]["expected_transfer_strategy"]
        task_results[task_id] = {
            "baseline_strategy": baseline_strategy,
            "selected_strategy": selected_strategy,
            "expected_transfer_strategy": expected,
            "transfer_prediction_match": selected_strategy == expected,
            "baseline_tokens": baseline["worker_tokens"],
            "selected_tokens": selected["worker_tokens"],
            "selected_performance_ratio_to_baseline": ratio,
            "gates": gates,
            "quality_passed": all(gates.values()),
        }
        baseline_tokens += baseline["worker_tokens"]
        selected_tokens += selected["worker_tokens"]
    all_acquired_valid = execution["status"] == "pass" and all(
        row["valid"] for row in rows
    )
    quality_passed = all_acquired_valid and all(
        result["quality_passed"] for result in task_results.values()
    )
    transfer_match_count = sum(
        result["transfer_prediction_match"] for result in task_results.values()
    )
    transfer_passed = transfer_match_count == len(task_results)
    acquisition = router["router_tokens"] + sum(
        row["worker_tokens"] for row in rows
    )
    marginal = evaluate_qualification_economics(
        acquisition_tokens=acquisition,
        baseline_deployment_tokens=baseline_tokens,
        candidate_deployment_tokens=selected_tokens,
        expected_deployments=protocol["expected_future_deployments"],
        correctness_passed=quality_passed,
        performance_passed=quality_passed,
        evidence_stable=quality_passed,
        minimum_saving_fraction=protocol["scoring"]["minimum_token_saving_fraction"],
    )
    lineage_acquisition = (
        protocol["economics"]["prior_experience_acquisition_tokens"] + acquisition
    )
    full_lineage = evaluate_qualification_economics(
        acquisition_tokens=lineage_acquisition,
        baseline_deployment_tokens=baseline_tokens,
        candidate_deployment_tokens=selected_tokens,
        expected_deployments=protocol["expected_future_deployments"],
        correctness_passed=quality_passed,
        performance_passed=quality_passed,
        evidence_stable=quality_passed,
        minimum_saving_fraction=protocol["scoring"]["minimum_token_saving_fraction"],
    )
    if not transfer_passed or not quality_passed:
        decision = "quality_fail"
    elif marginal["decision"] == "promote":
        decision = "pass_economic"
    else:
        decision = "quality_pass_economics_fail"
    report = {
        "schema": "modus-profile-experience-transfer-score-v1",
        "status": "pass" if all_acquired_valid else "fail",
        "rows": rows,
        "task_results": task_results,
        "selected_route": selected_route,
        "transfer_prediction_match_count": transfer_match_count,
        "transfer_prediction_task_count": len(task_results),
        "quality_passed": quality_passed,
        "deployment": {
            "fixed_strategy": baseline_strategy,
            "fixed_strategy_tokens": baseline_tokens,
            "selected_route_tokens": selected_tokens,
            "saving_tokens": baseline_tokens - selected_tokens,
            "saving_fraction": (
                1 - selected_tokens / baseline_tokens if baseline_tokens else None
            ),
        },
        "acquisition": {
            "router_tokens": router["router_tokens"],
            "worker_tokens": sum(row["worker_tokens"] for row in rows),
            "worker_cells": len(rows),
            "marginal_tokens": acquisition,
            "prior_experience_tokens": protocol["economics"]["prior_experience_acquisition_tokens"],
            "full_lineage_tokens": lineage_acquisition,
        },
        "marginal_economics": marginal,
        "full_lineage_economics": full_lineage,
        "decision": decision,
        "claim_boundary": (
            "This is a prospective transfer test against one frozen fixed "
            "strategy. Missing counterfactual strategies were not executed, so "
            "the result does not estimate a new complete-matrix Oracle."
        ),
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "selected_route": selected_route,
        "transfer_match_count": transfer_match_count,
        "quality_passed": quality_passed,
        "saving_fraction": report["deployment"]["saving_fraction"],
        "marginal_break_even": marginal["break_even_deployments"],
        "marginal_net_at_8": marginal["net_tokens_at_expected_deployments"],
        "full_lineage_break_even": full_lineage["break_even_deployments"],
        "decision": decision,
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

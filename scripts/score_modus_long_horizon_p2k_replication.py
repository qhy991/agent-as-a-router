#!/usr/bin/env python3
"""Combine the P2k reversed second pair with its noise-triggered first pair."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
for candidate in (SCRIPT_DIR, SOURCE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from acrouter_repro.qualification_economics import evaluate_qualification_economics  # noqa: E402
from score_modus_long_horizon_p2a_pipeline import (  # noqa: E402
    MAXIMUM_RELATIVE_MAD,
    MINIMUM_TOKEN_SAVING,
    PERFORMANCE_RATIO_MAXIMUM,
    _sha256,
    _wave_usage,
)


def _live_rows(root: Path, protocol: dict) -> list[dict]:
    rows = []
    for pipeline in protocol["pipelines"]:
        pipeline_root = root / "pipelines" / pipeline["id"]
        l_path = pipeline_root / "stage-l-verification.json"
        s_path = pipeline_root / "stage-s-verification.json"
        parent_path = pipeline_root / "stage-s-parent.json"
        stage_l = json.loads(l_path.read_text())
        stage_s = json.loads(s_path.read_text())
        parent = json.loads(parent_path.read_text())
        l_wave_ok, l_tokens = _wave_usage(pipeline_root / "stage-l-output/wave-result.json")
        s_wave_ok, s_tokens = _wave_usage(pipeline_root / "stage-s-output/wave-result.json")
        parent_bound = (
            parent["implementation_digest"] == stage_l["implementation_digest"]
            and parent["stage_l_verification_sha256"] == _sha256(l_path)
            and parent["implementation_files_sha256"] == stage_l["implementation_files_sha256"]
            and stage_s["parent_record"] == parent
        )
        rows.append({
            **pipeline,
            "valid": all((stage_l["passed"], stage_s["passed"], l_wave_ok, s_wave_ok, parent_bound)),
            "parent_bound": parent_bound,
            "stage_l_profile": stage_l["profile"],
            "stage_s_profile": stage_s["profile"],
            "stage_l_seconds": stage_l["benchmark"]["steady_seconds"],
            "final_seconds": stage_s["benchmark"]["steady_seconds"],
            "maximum_relative_mad": max(
                stage_l["benchmark"]["steady_relative_mad"],
                stage_s["benchmark"]["steady_relative_mad"],
            ),
            "worker_tokens": l_tokens + s_tokens,
            "stage_l_verification_sha256": _sha256(l_path),
            "stage_s_verification_sha256": _sha256(s_path),
            "parent_record_sha256": _sha256(parent_path),
        })
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.run_root.resolve()
    protocol = json.loads(args.protocol.read_text())
    repo = args.protocol.resolve().parents[1]
    initial = json.loads((repo / protocol["parent_initial"]["score_path"]).read_text())
    new_rows = _live_rows(root, protocol)
    rows = initial["pipelines"] + new_rows
    arms = {arm: [row for row in rows if row["arm"] == arm] for arm in ("proposed-route", "neutral")}
    aggregates = {}
    for arm, entries in arms.items():
        aggregates[arm] = {
            "pipelines": len(entries),
            "median_stage_l_seconds": statistics.median(row["stage_l_seconds"] for row in entries),
            "median_final_seconds": statistics.median(row["final_seconds"] for row in entries),
            "median_worker_tokens": statistics.median(row["worker_tokens"] for row in entries),
            "maximum_relative_mad": max(row["maximum_relative_mad"] for row in entries),
        }
    routed_ratio = (
        aggregates["proposed-route"]["median_final_seconds"]
        / min(value["median_final_seconds"] for value in aggregates.values())
    )
    stage_l_ratio = (
        aggregates["proposed-route"]["median_stage_l_seconds"]
        / min(value["median_stage_l_seconds"] for value in aggregates.values())
    )
    neutral_worker = aggregates["neutral"]["median_worker_tokens"]
    routed_worker = aggregates["proposed-route"]["median_worker_tokens"]
    router_tokens = protocol["parent_router"]["cached_tokens_per_deployment"]
    live_router_tokens = protocol["parent_router"]["live_tokens_per_deployment"]
    routed_e2e = routed_worker + router_tokens
    worker_saving = 1.0 - routed_worker / neutral_worker
    e2e_saving = 1.0 - routed_e2e / neutral_worker
    all_valid = all(row["valid"] for row in rows)
    second_arms = {
        arm: next(row for row in new_rows if row["arm"] == arm)
        for arm in ("proposed-route", "neutral")
    }
    second_stage_l_ratio = (
        second_arms["proposed-route"]["stage_l_seconds"]
        / min(row["stage_l_seconds"] for row in second_arms.values())
    )
    second_final_ratio = (
        second_arms["proposed-route"]["final_seconds"]
        / min(row["final_seconds"] for row in second_arms.values())
    )
    gates = {
        "all_four_pipelines_valid": all_valid and len(rows) == 4,
        "two_repetitions_per_arm": all(len(entries) == 2 for entries in arms.values()),
        "route_matches_frozen_profiles": protocol["arms"]["proposed-route"] == {
            "stage-L": "p000v2", "stage-S": "e1v2",
            "qualified_cached_router_calls_per_deployment": 0,
        },
        "first_pair_noise_trigger_bound": initial["trigger"] == {
            "triggered": True, "reasons": ["relative MAD exceeds 0.10"],
        },
        "second_pair_stage_l_performance": second_stage_l_ratio <= PERFORMANCE_RATIO_MAXIMUM,
        "second_pair_final_performance": second_final_ratio <= PERFORMANCE_RATIO_MAXIMUM,
        "stage_l_performance": stage_l_ratio <= PERFORMANCE_RATIO_MAXIMUM,
        "final_performance": routed_ratio <= PERFORMANCE_RATIO_MAXIMUM,
        "worker_token_saving": worker_saving >= MINIMUM_TOKEN_SAVING,
        "second_pair_noise_resolution": max(row["maximum_relative_mad"] for row in new_rows) <= MAXIMUM_RELATIVE_MAD,
    }
    new_acquisition = sum(row["worker_tokens"] for row in new_rows)
    total_acquisition = protocol["parent_initial"]["acquisition_tokens"] + new_acquisition
    qualified = all(gates.values())
    economics = evaluate_qualification_economics(
        acquisition_tokens=int(round(total_acquisition)),
        baseline_deployment_tokens=int(round(neutral_worker)),
        candidate_deployment_tokens=int(round(routed_e2e)),
        expected_deployments=protocol["expected_future_deployments"],
        correctness_passed=qualified,
        performance_passed=qualified,
        evidence_stable=qualified,
        minimum_saving_fraction=MINIMUM_TOKEN_SAVING,
    )
    report = {
        "schema": "modus-long-horizon-p2k-second-pair-score-v1",
        "status": "pass" if all_valid else "fail",
        "post_outcome_replication": True,
        "pipelines": rows,
        "aggregates": aggregates,
        "performance": {
            "stage_l_routed_ratio_to_fastest": stage_l_ratio,
            "final_routed_ratio_to_fastest": routed_ratio,
            "second_pair_stage_l_routed_ratio_to_fastest": second_stage_l_ratio,
            "second_pair_final_routed_ratio_to_fastest": second_final_ratio,
        },
        "deployment": {
            "neutral_worker_tokens": neutral_worker,
            "routed_worker_tokens": routed_worker,
            "worker_saving_fraction": worker_saving,
            "cached_router_tokens": router_tokens,
            "routed_e2e_tokens": routed_e2e,
            "e2e_saving_fraction": e2e_saving,
            "live_agent_counterfactual_tokens": routed_worker + live_router_tokens,
            "live_agent_counterfactual_saving_fraction": (
                1.0 - (routed_worker + live_router_tokens) / neutral_worker
            ),
        },
        "acquisition": {
            "initial_tokens": protocol["parent_initial"]["acquisition_tokens"],
            "second_pair_worker_tokens": new_acquisition,
            "combined_tokens": total_acquisition,
        },
        "gates": gates,
        "economics": economics,
        "proposal": {
            "actions": protocol["parent_router"]["actions"],
            "matches_preoutcome_oracle_topology": protocol["parent_router"]["actions"]
            == {"stage-L": "p000v2", "stage-S": "e1v2"},
        },
        "decision": (
            economics["decision"] if qualified
            else "stop_inconclusive_or_negative_no_further_replication"
        ),
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"], "decision": report["decision"],
        "final_performance_ratio": routed_ratio,
        "worker_saving_fraction": worker_saving,
        "e2e_saving_fraction": e2e_saving,
        "acquisition_tokens": total_acquisition,
        "break_even": economics["break_even_deployments"],
        "net_at_expected_deployments": economics["net_tokens_at_expected_deployments"],
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

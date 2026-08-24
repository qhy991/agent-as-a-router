#!/usr/bin/env python3
"""Score the first low-acquisition linked P2c routed/neutral pair."""

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
from score_modus_long_horizon_p2a_pipeline import _sha256, _wave_usage  # noqa: E402


PERFORMANCE_RATIO_MAXIMUM = 1.25
MINIMUM_TOKEN_SAVING = 0.15
MAXIMUM_RELATIVE_MAD = 0.10
AMBIGUITY_LOWER = 1.1875
AMBIGUITY_UPPER = 1.3125


def _row(root: Path, pipeline: dict) -> dict:
    pipeline_root = root / "pipelines" / pipeline["id"]
    l_path = pipeline_root / "stage-l-verification.json"
    s_path = pipeline_root / "stage-s-verification.json"
    parent_path = pipeline_root / "stage-s-parent.json"
    stage_l = json.loads(l_path.read_text())
    stage_s = json.loads(s_path.read_text())
    parent = json.loads(parent_path.read_text())
    l_ok, l_tokens = _wave_usage(pipeline_root / "stage-l-output/wave-result.json")
    s_ok, s_tokens = _wave_usage(pipeline_root / "stage-s-output/wave-result.json")
    parent_bound = (
        parent["implementation_digest"] == stage_l["implementation_digest"]
        and parent["stage_l_verification_sha256"] == _sha256(l_path)
        and stage_s["parent_record"] == parent
    )
    return {
        **pipeline,
        "valid": all((stage_l["passed"], stage_s["passed"], l_ok, s_ok, parent_bound)),
        "parent_bound": parent_bound,
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
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    protocol = json.loads(args.protocol.read_text())
    root = args.run_root.resolve()
    rows = [_row(root, pipeline) for pipeline in protocol["pipelines"]]
    routed = next(row for row in rows if row["arm"] == "routed")
    neutral = next(row for row in rows if row["arm"] == "neutral")
    final_ratio = routed["final_seconds"] / min(routed["final_seconds"], neutral["final_seconds"])
    stage_l_ratio = routed["stage_l_seconds"] / min(routed["stage_l_seconds"], neutral["stage_l_seconds"])
    worker_saving = 1.0 - routed["worker_tokens"] / neutral["worker_tokens"]
    router_tokens = protocol["parent_router"]["tokens_per_deployment"]
    routed_e2e = routed["worker_tokens"] + router_tokens
    e2e_saving = 1.0 - routed_e2e / neutral["worker_tokens"]
    trigger_reasons = []
    if routed["valid"] != neutral["valid"]:
        trigger_reasons.append("pipeline quality disagreement")
    if AMBIGUITY_LOWER <= final_ratio <= AMBIGUITY_UPPER:
        trigger_reasons.append("final performance is within five percent of 1.25x")
    if max(row["maximum_relative_mad"] for row in rows) > MAXIMUM_RELATIVE_MAD:
        trigger_reasons.append("relative MAD exceeds 0.10")
    gates = {
        "both_pipelines_valid": all(row["valid"] for row in rows),
        "stage_l_performance": stage_l_ratio <= PERFORMANCE_RATIO_MAXIMUM,
        "final_performance": final_ratio <= PERFORMANCE_RATIO_MAXIMUM,
        "worker_token_saving": worker_saving >= MINIMUM_TOKEN_SAVING,
        "noise": max(row["maximum_relative_mad"] for row in rows) <= MAXIMUM_RELATIVE_MAD,
    }
    acquisition = protocol["parent_router"]["acquisition_tokens"] + sum(
        row["worker_tokens"] for row in rows
    )
    qualified = all(gates.values()) and not trigger_reasons
    economics = evaluate_qualification_economics(
        acquisition_tokens=int(round(acquisition)),
        baseline_deployment_tokens=int(round(neutral["worker_tokens"])),
        candidate_deployment_tokens=int(round(routed_e2e)),
        expected_deployments=protocol["expected_future_deployments"],
        correctness_passed=qualified,
        performance_passed=qualified,
        evidence_stable=qualified,
        minimum_saving_fraction=MINIMUM_TOKEN_SAVING,
    )
    if trigger_reasons:
        decision = "second_pair_required"
    elif not qualified:
        decision = "stop_negative"
    else:
        decision = economics["decision"]
    report = {
        "schema": "modus-long-horizon-p2c-first-pair-score-v1",
        "status": "pass" if all(row["valid"] for row in rows) else "fail",
        "pipelines": rows,
        "performance": {
            "stage_l_routed_ratio_to_fastest": stage_l_ratio,
            "final_routed_ratio_to_fastest": final_ratio,
        },
        "deployment": {
            "neutral_worker_tokens": neutral["worker_tokens"],
            "routed_worker_tokens": routed["worker_tokens"],
            "worker_saving_fraction": worker_saving,
            "live_router_tokens": router_tokens,
            "routed_e2e_tokens": routed_e2e,
            "e2e_saving_fraction": e2e_saving,
        },
        "acquisition_tokens": acquisition,
        "trigger": {"triggered": bool(trigger_reasons), "reasons": trigger_reasons},
        "gates": gates,
        "economics": economics,
        "decision": decision,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"], "decision": decision,
        "final_performance_ratio": final_ratio,
        "worker_saving_fraction": worker_saving,
        "e2e_saving_fraction": e2e_saving,
        "acquisition_tokens": acquisition,
        "break_even": economics["break_even_deployments"],
        "net_at_expected_deployments": economics["net_tokens_at_expected_deployments"],
        "trigger": trigger_reasons,
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

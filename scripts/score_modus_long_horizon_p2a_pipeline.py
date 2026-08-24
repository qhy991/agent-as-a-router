#!/usr/bin/env python3
"""Score balanced linked P2a pipelines and Router-inclusive economics."""

from __future__ import annotations

import argparse
import hashlib
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
MINIMUM_TOKEN_SAVING = 0.15
MAXIMUM_RELATIVE_MAD = 0.10
AMBIGUITY_LOWER = 1.1875
AMBIGUITY_UPPER = 1.3125


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _usage_tokens(usage: dict) -> int | None:
    if not isinstance(usage, dict):
        return None
    if not all(isinstance(usage.get(key), int) for key in ("input_tokens", "output_tokens")):
        return None
    return usage["input_tokens"] + usage["output_tokens"]


def _wave_usage(path: Path) -> tuple[bool, int | None]:
    value = json.loads(path.read_text())
    if value.get("status") != "pass" or len(value.get("cells", [])) != 1:
        return False, None
    cell = value["cells"][0]
    return bool(cell["valid_execution"]), _usage_tokens(cell.get("usage"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.run_root.resolve()
    protocol = json.loads(args.protocol.read_text())
    rows = []
    for pipeline in protocol["pipelines"]:
        pipeline_root = root / "pipelines" / pipeline["id"]
        stage_l_path = pipeline_root / "stage-l-verification.json"
        stage_s_path = pipeline_root / "stage-s-verification.json"
        parent_path = pipeline_root / "stage-s-parent.json"
        stage_l = json.loads(stage_l_path.read_text())
        stage_s = json.loads(stage_s_path.read_text())
        parent = json.loads(parent_path.read_text())
        l_wave_ok, l_tokens = _wave_usage(
            pipeline_root / "stage-l-output" / "wave-result.json"
        )
        s_wave_ok, s_tokens = _wave_usage(
            pipeline_root / "stage-s-output" / "wave-result.json"
        )
        parent_bound = (
            parent.get("schema") == "modus-long-horizon-p2a-parent-v1"
            and parent.get("implementation_digest") == stage_l["implementation_digest"]
            and parent.get("stage_l_verification_sha256") == _sha256(stage_l_path)
            and stage_s.get("parent_record") == parent
        )
        valid = all((
            stage_l["passed"], stage_s["passed"], l_wave_ok, s_wave_ok,
            l_tokens is not None, s_tokens is not None, parent_bound,
        ))
        rows.append({
            "id": pipeline["id"], "pair": pipeline["pair"],
            "order": pipeline["order"], "arm": pipeline["arm"],
            "valid": valid, "parent_bound": parent_bound,
            "stage_l_profile": stage_l["profile"],
            "stage_s_profile": stage_s["profile"],
            "stage_l_seconds": stage_l["benchmark"].get("steady_seconds"),
            "final_seconds": stage_s["benchmark"].get("steady_seconds"),
            "maximum_relative_mad": max(
                stage_l["benchmark"].get("steady_relative_mad", 1.0),
                stage_s["benchmark"].get("steady_relative_mad", 1.0),
            ),
            "worker_tokens": l_tokens + s_tokens if l_tokens is not None and s_tokens is not None else None,
            "stage_l_verification_sha256": _sha256(stage_l_path),
            "stage_s_verification_sha256": _sha256(stage_s_path),
            "parent_record_sha256": _sha256(parent_path),
        })
    all_valid = all(row["valid"] for row in rows)
    arms = {
        arm: [row for row in rows if row["arm"] == arm]
        for arm in ("routed", "neutral")
    }
    aggregates = {}
    for arm, entries in arms.items():
        aggregates[arm] = {
            "pipelines": len(entries),
            "median_stage_l_seconds": statistics.median(row["stage_l_seconds"] for row in entries),
            "median_final_seconds": statistics.median(row["final_seconds"] for row in entries),
            "median_worker_tokens": statistics.median(row["worker_tokens"] for row in entries),
            "maximum_relative_mad": max(row["maximum_relative_mad"] for row in entries),
        }
    fastest_final = min(value["median_final_seconds"] for value in aggregates.values())
    routed_ratio = aggregates["routed"]["median_final_seconds"] / fastest_final
    stage_l_ratio = (
        aggregates["routed"]["median_stage_l_seconds"]
        / min(value["median_stage_l_seconds"] for value in aggregates.values())
    )
    routed_worker = aggregates["routed"]["median_worker_tokens"]
    neutral_worker = aggregates["neutral"]["median_worker_tokens"]
    router_tokens = protocol["parent_router"]["tokens_per_deployment"]
    routed_e2e = routed_worker + router_tokens
    worker_saving = 1.0 - routed_worker / neutral_worker
    e2e_saving = 1.0 - routed_e2e / neutral_worker
    paired_ratios = []
    for pair in (1, 2):
        routed = next(row for row in rows if row["pair"] == pair and row["arm"] == "routed")
        neutral = next(row for row in rows if row["pair"] == pair and row["arm"] == "neutral")
        paired_ratios.append(routed["final_seconds"] / neutral["final_seconds"])
    ambiguity_reasons = []
    if min(paired_ratios) <= PERFORMANCE_RATIO_MAXIMUM < max(paired_ratios):
        ambiguity_reasons.append("paired final-performance ratios straddle 1.25x")
    if AMBIGUITY_LOWER <= routed_ratio <= AMBIGUITY_UPPER:
        ambiguity_reasons.append("aggregate final ratio is within five percent of 1.25x")
    if max(value["maximum_relative_mad"] for value in aggregates.values()) > MAXIMUM_RELATIVE_MAD:
        ambiguity_reasons.append("relative MAD exceeds 0.10")
    gates = {
        "all_pipelines_valid": all_valid,
        "balanced_ab_ba": [(row["pair"], row["order"], row["arm"]) for row in rows] == [
            (1, 1, "routed"), (1, 2, "neutral"),
            (2, 1, "neutral"), (2, 2, "routed"),
        ],
        "stage_l_performance": stage_l_ratio <= PERFORMANCE_RATIO_MAXIMUM,
        "final_performance": routed_ratio <= PERFORMANCE_RATIO_MAXIMUM,
        "worker_token_saving": worker_saving >= MINIMUM_TOKEN_SAVING,
        "no_ambiguity_trigger": not ambiguity_reasons,
    }
    worker_acquisition = sum(row["worker_tokens"] for row in rows)
    total_acquisition = protocol["parent_router"]["acquisition_tokens"] + worker_acquisition
    qualification = all(gates.values())
    economics = evaluate_qualification_economics(
        acquisition_tokens=int(round(total_acquisition)),
        baseline_deployment_tokens=int(round(neutral_worker)),
        candidate_deployment_tokens=int(round(routed_e2e)),
        expected_deployments=protocol["expected_future_deployments"],
        correctness_passed=qualification,
        performance_passed=qualification,
        evidence_stable=qualification,
        minimum_saving_fraction=MINIMUM_TOKEN_SAVING,
    )
    decision = (
        "third_paired_replication_required" if ambiguity_reasons
        else economics["decision"]
    )
    report = {
        "schema": "modus-long-horizon-p2a-pipeline-score-v1",
        "status": "pass" if all_valid else "fail",
        "pipelines": rows,
        "aggregates": aggregates,
        "performance": {
            "stage_l_routed_ratio_to_fastest": stage_l_ratio,
            "final_routed_ratio_to_fastest": routed_ratio,
            "paired_final_routed_to_neutral_ratios": paired_ratios,
        },
        "deployment": {
            "neutral_worker_tokens": neutral_worker,
            "routed_worker_tokens": routed_worker,
            "worker_saving_fraction": worker_saving,
            "live_router_tokens": router_tokens,
            "routed_e2e_tokens": routed_e2e,
            "e2e_saving_fraction": e2e_saving,
        },
        "acquisition": {
            "router_tokens": protocol["parent_router"]["acquisition_tokens"],
            "worker_tokens": worker_acquisition,
            "total_tokens": total_acquisition,
        },
        "ambiguity": {"triggered": bool(ambiguity_reasons), "reasons": ambiguity_reasons},
        "gates": gates,
        "economics": economics,
        "decision": decision,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"], "decision": decision,
        "final_performance_ratio": routed_ratio,
        "worker_saving_fraction": worker_saving,
        "e2e_saving_fraction": e2e_saving,
        "acquisition_tokens": total_acquisition,
        "break_even": economics["break_even_deployments"],
        "net_at_expected_deployments": economics["net_tokens_at_expected_deployments"],
        "ambiguity": ambiguity_reasons,
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Combine the P2l reversed second triplet with its triggered first triplet."""

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


def _new_rows(root: Path, protocol: dict) -> list[dict]:
    rows = []
    for cell in protocol["cells"]:
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
    new_rows = _new_rows(root, protocol)
    rows = initial["rows"] + new_rows
    by_profile = {
        profile: [row for row in rows if row["profile"] == profile]
        for profile in ("neutral", "e1v2", "e1v3")
    }
    aggregates = {}
    for profile, entries in by_profile.items():
        aggregates[profile] = {
            "repetitions": len(entries),
            "valid_repetitions": sum(row["valid"] for row in entries),
            "median_seconds": statistics.median(row["seconds"] for row in entries),
            "median_worker_tokens": statistics.median(row["worker_tokens"] for row in entries),
            "maximum_relative_mad": max(row["relative_mad"] for row in entries),
        }
    neutral = aggregates["neutral"]
    candidates = {}
    for profile in ("e1v2", "e1v3"):
        aggregate = aggregates[profile]
        per_repetition = []
        for triplet in (1, 2):
            candidate_row = next(row for row in by_profile[profile] if row["triplet"] == triplet)
            neutral_row = next(row for row in by_profile["neutral"] if row["triplet"] == triplet)
            per_repetition.append(candidate_row["seconds"] / neutral_row["seconds"])
        performance_ratio = aggregate["median_seconds"] / neutral["median_seconds"]
        token_saving = 1.0 - aggregate["median_worker_tokens"] / neutral["median_worker_tokens"]
        gates = {
            "two_valid_repetitions": aggregate["valid_repetitions"] == 2,
            "median_performance": performance_ratio <= PERFORMANCE_RATIO_MAXIMUM,
            "per_repetition_performance": max(per_repetition) <= PERFORMANCE_RATIO_MAXIMUM,
            "token_saving": token_saving >= MINIMUM_TOKEN_SAVING,
        }
        if profile == "e1v3":
            second_rows = [
                next(row for row in by_profile[name] if row["triplet"] == 2)
                for name in ("neutral", "e1v3")
            ]
            gates["second_triplet_noise_resolution"] = (
                max(row["relative_mad"] for row in second_rows) <= MAXIMUM_RELATIVE_MAD
            )
        else:
            gates["second_triplet_noise_resolution"] = True
        candidates[profile] = {
            "performance_ratio_to_neutral": performance_ratio,
            "per_repetition_performance_ratios": per_repetition,
            "token_saving_fraction_vs_neutral": token_saving,
            "gates": gates,
            "eligible": all(gates.values()),
        }

    eligible_profiles = [
        profile for profile in ("e1v2", "e1v3") if candidates[profile]["eligible"]
    ]
    selected = min(
        eligible_profiles,
        key=lambda profile: aggregates[profile]["median_worker_tokens"],
        default=None,
    )
    if selected == "e1v3":
        decision = "promote_e1v3_to_p2m"
    elif selected == "e1v2":
        decision = "retain_e1v2_for_p2m"
    else:
        decision = "stop_no_eligible_coordinated_profile"
    acquisition = protocol["parent_initial"]["acquisition_tokens"] + sum(
        row["worker_tokens"] for row in new_rows
    )
    selected_tokens = (
        aggregates[selected]["median_worker_tokens"]
        if selected else aggregates["e1v3"]["median_worker_tokens"]
    )
    economics = evaluate_qualification_economics(
        acquisition_tokens=int(round(acquisition)),
        baseline_deployment_tokens=int(round(neutral["median_worker_tokens"])),
        candidate_deployment_tokens=int(round(selected_tokens)),
        expected_deployments=protocol["expected_future_deployments"],
        correctness_passed=selected is not None,
        performance_passed=selected is not None,
        evidence_stable=selected is not None,
        minimum_saving_fraction=MINIMUM_TOKEN_SAVING,
    )
    report = {
        "schema": "modus-performance-p2l-second-triplet-score-v1",
        "status": "pass" if all(
            next(row for row in new_rows if row["profile"] == profile)["valid"]
            for profile in ("neutral", "e1v3")
        ) else "fail",
        "post_outcome_replication": True,
        "rows": rows,
        "aggregates": aggregates,
        "candidates": candidates,
        "selected_profile": selected,
        "acquisition_tokens": acquisition,
        "economics": economics,
        "decision": decision,
        "no_further_replication": True,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "decision": decision,
        "selected_profile": selected,
        "e1v2": candidates["e1v2"],
        "e1v3": candidates["e1v3"],
        "acquisition_tokens": acquisition,
        "break_even": economics["break_even_deployments"],
        "net_at_8": economics["net_tokens_at_expected_deployments"],
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

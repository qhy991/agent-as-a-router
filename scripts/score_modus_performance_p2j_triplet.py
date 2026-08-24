#!/usr/bin/env python3
"""Score the frozen P2j neutral/p000/p000-v2 triplet."""

from __future__ import annotations

import argparse
import json
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


def _row(root: Path, cell: dict) -> dict:
    cell_root = root / "cells" / cell["id"]
    verification_path = cell_root / "verification.json"
    verification = json.loads(verification_path.read_text())
    usage_ok, tokens = _wave_usage(cell_root / "output/wave-result.json")
    return {
        **cell,
        "valid": verification["passed"] and usage_ok,
        "seconds": verification["benchmark"]["steady_seconds"],
        "relative_mad": verification["benchmark"]["steady_relative_mad"],
        "worker_tokens": tokens,
        "implementation_digest": verification["implementation_digest"],
        "verification_sha256": _sha256(verification_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    protocol = json.loads(args.protocol.read_text())
    root = args.run_root.resolve()
    rows = [_row(root, cell) for cell in protocol["cells"]]
    by_profile = {row["profile"]: row for row in rows}
    neutral = by_profile["neutral"]
    candidates = {}
    for profile in ("p000", "p000v2"):
        row = by_profile[profile]
        performance_ratio = row["seconds"] / neutral["seconds"]
        token_saving = 1.0 - row["worker_tokens"] / neutral["worker_tokens"]
        gates = {
            "valid": row["valid"] and neutral["valid"],
            "performance": performance_ratio <= PERFORMANCE_RATIO_MAXIMUM,
            "token_saving": token_saving >= MINIMUM_TOKEN_SAVING,
            "noise": max(row["relative_mad"], neutral["relative_mad"]) <= MAXIMUM_RELATIVE_MAD,
        }
        candidates[profile] = {
            "performance_ratio_to_neutral": performance_ratio,
            "token_saving_fraction_vs_neutral": token_saving,
            "gates": gates,
            "eligible": all(gates.values()),
        }

    v2 = candidates["p000v2"]
    trigger_reasons = []
    if len({row["valid"] for row in rows}) != 1:
        trigger_reasons.append("cell quality disagreement")
    if max(row["relative_mad"] for row in rows) > MAXIMUM_RELATIVE_MAD:
        trigger_reasons.append("relative MAD exceeds 0.10")
    if 1.1875 <= v2["performance_ratio_to_neutral"] <= 1.3125:
        trigger_reasons.append("p000-v2 performance is within five percent of 1.25x")
    if 0.10 <= v2["token_saving_fraction_vs_neutral"] <= 0.20:
        trigger_reasons.append("p000-v2 token saving is within five points of 15 percent")

    eligible_profiles = [
        profile for profile in ("p000", "p000v2") if candidates[profile]["eligible"]
    ]
    selected = min(
        eligible_profiles,
        key=lambda profile: by_profile[profile]["worker_tokens"],
        default=None,
    )
    if trigger_reasons:
        decision = "second_triplet_required"
    elif selected == "p000v2":
        decision = "promote_p000v2_to_p2k"
    elif selected == "p000":
        decision = "retain_p000_for_p2k"
    else:
        decision = "stop_no_eligible_target_only_profile"

    acquisition = sum(row["worker_tokens"] for row in rows)
    selected_tokens = by_profile[selected]["worker_tokens"] if selected else by_profile["p000v2"]["worker_tokens"]
    economics = evaluate_qualification_economics(
        acquisition_tokens=acquisition,
        baseline_deployment_tokens=neutral["worker_tokens"],
        candidate_deployment_tokens=selected_tokens,
        expected_deployments=protocol["expected_future_deployments"],
        correctness_passed=selected is not None and not trigger_reasons,
        performance_passed=selected is not None and not trigger_reasons,
        evidence_stable=selected is not None and not trigger_reasons,
        minimum_saving_fraction=MINIMUM_TOKEN_SAVING,
    )
    p000 = by_profile["p000"]
    p000v2 = by_profile["p000v2"]
    report = {
        "schema": "modus-performance-p2j-triplet-score-v1",
        "status": "pass" if all(row["valid"] for row in rows) else "fail",
        "rows": rows,
        "candidates": candidates,
        "profile_revision_effect": {
            "implementation_digest_differs": p000["implementation_digest"] != p000v2["implementation_digest"],
            "p000v2_seconds_ratio_to_p000": p000v2["seconds"] / p000["seconds"],
            "p000v2_tokens_ratio_to_p000": p000v2["worker_tokens"] / p000["worker_tokens"],
        },
        "selected_profile": selected,
        "acquisition_tokens": acquisition,
        "trigger": {"triggered": bool(trigger_reasons), "reasons": trigger_reasons},
        "economics": economics,
        "decision": decision,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "decision": decision,
        "selected_profile": selected,
        "p000": candidates["p000"],
        "p000v2": candidates["p000v2"],
        "acquisition_tokens": acquisition,
        "break_even": economics["break_even_deployments"],
        "net_at_8": economics["net_tokens_at_expected_deployments"],
        "trigger": trigger_reasons,
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

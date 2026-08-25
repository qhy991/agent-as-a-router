#!/usr/bin/env python3
"""Score invariant-specialization behavior manipulation without utility promotion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
for candidate in (SCRIPT_DIR, SCRIPT_DIR.parent / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from score_modus_long_horizon_p2a_pipeline import _sha256, _wave_usage  # noqa: E402


CANDIDATE = "invariant-specialized-optimization"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.run_root.resolve()
    protocol = json.loads(args.protocol.read_text())
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
            "correctness": verification["checks"]["correctness"],
            "custody": verification["checks"]["custody"],
            "behavior": verification["behavior"],
            "seconds": verification["benchmark"]["steady_seconds"],
            "relative_mad": verification["benchmark"]["steady_relative_mad"],
            "worker_tokens": tokens,
            "implementation_digest": verification["implementation_digest"],
            "verification_sha256": _sha256(verification_path),
        })
    candidate_rows = [row for row in rows if row["strategy"] == CANDIDATE]
    counts = {
        "candidate_cells": len(candidate_rows),
        "candidate_correct": sum(row["correctness"] for row in candidate_rows),
        "candidate_topology_exact": sum(
            row["behavior"]["topology_exact"] for row in candidate_rows
        ),
        "candidate_prepared_semantics": sum(
            row["behavior"]["runtime_prepared_semantics"] for row in candidate_rows
        ),
        "candidate_preparation_once": sum(
            row["behavior"]["preparation_once"] for row in candidate_rows
        ),
        "candidate_target_invariants_absent": sum(
            row["behavior"]["target_invariants_absent"] for row in candidate_rows
        ),
        "candidate_no_data_index": sum(
            row["behavior"]["no_data_dependent_index"] for row in candidate_rows
        ),
        "candidate_noise_pass": sum(
            row["relative_mad"] is not None and row["relative_mad"] <= 0.10
            for row in candidate_rows
        ),
        "all_valid_cells": sum(row["valid"] for row in rows),
    }
    gates = {
        "candidate_correct_8_of_8": counts["candidate_correct"] == 8,
        "candidate_topology_8_of_8": counts["candidate_topology_exact"] == 8,
        "candidate_prepared_semantics_8_of_8": counts["candidate_prepared_semantics"] == 8,
        "candidate_preparation_once_8_of_8": counts["candidate_preparation_once"] == 8,
        "candidate_target_invariants_absent_7_of_8": counts["candidate_target_invariants_absent"] >= 7,
        "candidate_no_data_index_8_of_8": counts["candidate_no_data_index"] == 8,
        "candidate_noise_7_of_8": counts["candidate_noise_pass"] >= 7,
        "complete_valid_matrix_24_of_24": counts["all_valid_cells"] == 24,
        "automatic_redispatches_zero": execution["automatic_redispatches"] == 0,
    }
    diagnostics = {}
    for task_id in protocol["tasks"]:
        task_rows = [row for row in rows if row["task_id"] == task_id]
        diagnostics[task_id] = {
            strategy: {
                "median_tokens": statistics.median(
                    row["worker_tokens"] for row in task_rows
                    if row["strategy"] == strategy
                ),
                "median_seconds": statistics.median(
                    row["seconds"] for row in task_rows
                    if row["strategy"] == strategy
                ),
            }
            for strategy in protocol["strategies"]
        }
    passed = len(candidate_rows) == 8 and all(gates.values())
    report = {
        "schema": "modus-invariant-specialization-manipulation-score-v1",
        "status": "pass" if execution["status"] == "pass" else "fail",
        "rows": rows,
        "counts": counts,
        "gates": gates,
        "manipulation_passed": passed,
        "diagnostic_only": {
            "performance_and_tokens": diagnostics,
            "total_worker_tokens": sum(row["worker_tokens"] for row in rows),
        },
        "decision": (
            "authorize_independent_cpu_utility_holdout"
            if passed else "reject_or_allow_one_development_text_revision"
        ),
        "profile_status_after_result": (
            "manipulation-qualified-utility-unqualified"
            if passed else "unqualified-development-candidate"
        ),
        "claim_boundary": (
            "This development experiment may qualify behavior manipulation only. "
            "Performance and token values are diagnostic and cannot establish "
            "task utility, Router eligibility, CPU transfer, or GPU value."
        ),
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "counts": counts,
        "manipulation_passed": passed,
        "decision": report["decision"],
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

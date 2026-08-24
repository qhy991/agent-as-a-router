#!/usr/bin/env python3
"""Build the derived cross-experiment Modus scorecard from canonical artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ARTIFACTS = Path("agentic-artifacts")


def _source(root: Path, name: str) -> tuple[dict, dict]:
    path = root / ARTIFACTS / name
    return json.loads(path.read_text()), {
        "path": f"agentic-artifacts/{name}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def build(root: Path) -> dict:
    p1e, p1e_source = _source(root, "modus-codex-luna-max-reachability-p1e-final-v1.json")
    p1f, p1f_source = _source(root, "modus-codex-luna-max-connectivity-p1f-replicated-v1.json")
    p2a, p2a_source = _source(root, "modus-codex-luna-max-long-horizon-p2a-final-v1.json")
    p2b, p2b_source = _source(root, "modus-codex-luna-max-long-horizon-p2b-transfer-v1.json")
    p2c, p2c_source = _source(root, "modus-codex-luna-max-long-horizon-p2c-transfer-v1.json")
    p2d, p2d_source = _source(root, "modus-codex-luna-max-long-horizon-p2d-final-v1.json")
    p2h, p2h_source = _source(root, "modus-codex-luna-max-long-horizon-p2h-invalid-v1.json")

    p1f_max_ratio = max(
        row.get("p000_performance_ratio", row.get("e1v2_performance_ratio"))
        for row in p1f["replicated_tasks"].values()
    )
    rows = [
        {
            "experiment": "P1e",
            "task_family": "reachability",
            "workflow": "two independent stage-selection tasks",
            "route": {"x01": "p000", "x02": "neutral"},
            "evidence_status": "development_outcome",
            "outcome_valid": True,
            "route_qualified": True,
            "final_performance_ratio_to_fastest": None,
            "worker_saving_fraction": p1e["final_route"]["saving_fraction_vs_best_fixed"],
            "e2e_saving_fraction": None,
            "acquisition_tokens": p1e["end_to_end_economics"]["total_acquisition_tokens"],
            "break_even_deployments": p1e["end_to_end_economics"]["break_even_deployments"],
            "net_tokens_at_8_deployments": p1e["end_to_end_economics"]["net_tokens_at_expected_deployments"],
            "source": p1e_source,
        },
        {
            "experiment": "P1f",
            "task_family": "connectivity",
            "workflow": "replicated two-task Agent routing",
            "route": {"y01": "p000", "y02": "e1v2"},
            "evidence_status": "replicated_preliminary",
            "outcome_valid": True,
            "route_qualified": True,
            "final_performance_ratio_to_fastest": p1f_max_ratio,
            "worker_saving_fraction": p1f["deployment"]["worker_saving_fraction"],
            "e2e_saving_fraction": p1f["deployment"]["e2e_saving_fraction"],
            "acquisition_tokens": p1f["economics"]["combined_acquisition_tokens"],
            "break_even_deployments": p1f["economics"]["break_even_deployments"],
            "net_tokens_at_8_deployments": p1f["economics"]["net_tokens_at_expected_deployments"],
            "source": p1f_source,
        },
        {
            "experiment": "P2a",
            "task_family": "connectivity",
            "workflow": "replicated linked Stage L to Stage S",
            "route": {"stage-L": "p000", "stage-S": "e1v2"},
            "evidence_status": "replicated_linked_case",
            "outcome_valid": True,
            "route_qualified": True,
            "final_performance_ratio_to_fastest": p2a["replicated_aggregates"]["routed_final_ratio_to_fastest"],
            "worker_saving_fraction": p2a["replicated_aggregates"]["worker_saving_fraction"],
            "e2e_saving_fraction": p2a["replicated_aggregates"]["e2e_saving_fraction"],
            "acquisition_tokens": p2a["economics"]["combined_acquisition_tokens"],
            "break_even_deployments": p2a["economics"]["break_even_deployments"],
            "net_tokens_at_8_deployments": p2a["economics"]["net_tokens_at_expected_deployments"],
            "source": p2a_source,
        },
        {
            "experiment": "P2b",
            "task_family": "rangesum",
            "workflow": "one-pair linked transfer",
            "route": {"stage-L": "p000", "stage-S": "e1v2"},
            "evidence_status": "prospective_low_acquisition",
            "outcome_valid": True,
            "route_qualified": True,
            "final_performance_ratio_to_fastest": p2b["performance"]["routed_final_ratio_to_fastest"],
            "worker_saving_fraction": p2b["deployment"]["worker_saving_fraction"],
            "e2e_saving_fraction": p2b["deployment"]["e2e_saving_fraction"],
            "acquisition_tokens": p2b["economics"]["total_acquisition_tokens"],
            "break_even_deployments": p2b["economics"]["break_even_deployments"],
            "net_tokens_at_8_deployments": p2b["economics"]["net_tokens_at_expected_deployments"],
            "source": p2b_source,
        },
        {
            "experiment": "P2c",
            "task_family": "token_frequency",
            "workflow": "one-pair linked transfer",
            "route": {"stage-L": "p000", "stage-S": "e1v2"},
            "evidence_status": "prospective_low_acquisition",
            "outcome_valid": True,
            "route_qualified": True,
            "final_performance_ratio_to_fastest": p2c["performance"]["routed_final_ratio_to_fastest"],
            "worker_saving_fraction": p2c["deployment"]["worker_saving_fraction"],
            "e2e_saving_fraction": p2c["deployment"]["live_router_e2e_saving_fraction"],
            "acquisition_tokens": p2c["primary_economics"]["acquisition_tokens"],
            "break_even_deployments": p2c["primary_economics"]["break_even_deployments"],
            "net_tokens_at_8_deployments": p2c["primary_economics"]["net_tokens_at_expected_deployments"],
            "source": p2c_source,
        },
        {
            "experiment": "P2d",
            "task_family": "membership",
            "workflow": "replicated cached linked route",
            "route": {"stage-L": "e1v2", "stage-S": "p000"},
            "evidence_status": "prospective_replicated_negative",
            "outcome_valid": True,
            "route_qualified": False,
            "final_performance_ratio_to_fastest": p2d["replicated_aggregates"]["routed_final_ratio_to_fastest"],
            "worker_saving_fraction": p2d["replicated_aggregates"]["worker_saving_fraction"],
            "e2e_saving_fraction": p2d["replicated_aggregates"]["worker_saving_fraction"],
            "acquisition_tokens": p2d["economics"]["combined_acquisition_tokens"],
            "break_even_deployments": p2d["economics"]["break_even_deployments"],
            "net_tokens_at_8_deployments": p2d["economics"]["net_tokens_at_expected_deployments"],
            "source": p2d_source,
        },
        {
            "experiment": "P2h",
            "task_family": "distinct_out_degree",
            "workflow": "scratch qualification after Agent proposal",
            "route": p2h["agent_proposal"]["actions"],
            "evidence_status": p2h["formal_status"],
            "outcome_valid": False,
            "route_qualified": False,
            "final_performance_ratio_to_fastest": p2h["exploratory_only"]["final_proposed_ratio_to_fastest"],
            "worker_saving_fraction": p2h["exploratory_only"]["worker_token_saving_fraction"],
            "e2e_saving_fraction": None,
            "acquisition_tokens": p2h["exploratory_only"]["acquisition_tokens"],
            "break_even_deployments": None,
            "net_tokens_at_8_deployments": None,
            "excluded_from_valid_trends": True,
            "source": p2h_source,
        },
    ]
    valid = [row for row in rows if row["outcome_valid"]]
    return {
        "schema": "modus-experiment-scorecard-v1",
        "derived_view": True,
        "canonical_owner": "the source artifact named in each row",
        "common_contract": {
            "correctness_and_mechanism_gate_before_cost": True,
            "performance_ratio_maximum": 1.25,
            "relative_mad_maximum": 0.10,
            "minimum_token_saving_fraction": 0.15,
            "economic_horizon_deployments": 8,
            "invalid_runs_excluded_from_valid_trends": True,
        },
        "summary": {
            "rows": len(rows),
            "valid_outcomes": len(valid),
            "invalid_outcomes": len(rows) - len(valid),
            "qualified_routes": sum(row["route_qualified"] for row in valid),
            "net_positive_at_8_deployments": sum(
                (row["net_tokens_at_8_deployments"] or 0) > 0 for row in valid
            ),
        },
        "experiments": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = build(args.root.resolve())
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()

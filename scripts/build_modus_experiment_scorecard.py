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
    p2i, p2i_source = _source(root, "modus-codex-luna-max-long-horizon-p2i-negative-v1.json")
    p2j, p2j_source = _source(root, "modus-codex-luna-max-performance-p2j-positive-v1.json")
    p2k, p2k_source = _source(root, "modus-codex-luna-max-long-horizon-p2k-final-v1.json")
    p2l, p2l_source = _source(root, "modus-codex-luna-max-performance-p2l-final-v1.json")
    p2n, p2n_source = _source(root, "modus-codex-luna-max-performance-p2n-partial-v1.json")
    p2p, p2p_source = _source(root, "modus-codex-luna-max-performance-p2p-positive-v1.json")

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
        {
            "experiment": "P2i",
            "task_family": "keyed_max",
            "workflow": "observable-contract scratch qualification",
            "route": p2i["agent_proposal"]["actions"],
            "evidence_status": p2i["formal_status"],
            "outcome_valid": True,
            "route_qualified": False,
            "final_performance_ratio_to_fastest": p2i["common_metrics"]["final_proposed_ratio_to_fastest"],
            "worker_saving_fraction": p2i["common_metrics"]["worker_token_saving_fraction"],
            "e2e_saving_fraction": p2i["common_metrics"]["worker_token_saving_fraction"],
            "acquisition_tokens": p2i["common_metrics"]["acquisition_tokens"],
            "break_even_deployments": None,
            "net_tokens_at_8_deployments": None,
            "disqualification": "stage_l_performance_ratio_exceeds_1.25",
            "source": p2i_source,
        },
        {
            "experiment": "P2j",
            "task_family": "group_distinct",
            "workflow": "single-stage Profile revision triplet",
            "route": {"stage-L": "p000v2"},
            "evidence_status": p2j["formal_status"],
            "outcome_valid": True,
            "route_qualified": True,
            "final_performance_ratio_to_fastest": p2j["common_metrics"]["p000v2_performance_ratio_to_neutral"],
            "worker_saving_fraction": p2j["common_metrics"]["p000v2_token_saving_fraction_vs_neutral"],
            "e2e_saving_fraction": p2j["common_metrics"]["p000v2_token_saving_fraction_vs_neutral"],
            "acquisition_tokens": p2j["common_metrics"]["acquisition_tokens"],
            "break_even_deployments": p2j["common_metrics"]["break_even_deployments"],
            "net_tokens_at_8_deployments": p2j["common_metrics"]["net_tokens_at_8_deployments"],
            "source": p2j_source,
        },
        {
            "experiment": "P2k",
            "task_family": "keyed_distinct_sum",
            "workflow": "replicated revised-Profile linked route",
            "route": {"stage-L": "p000v2", "stage-S": "e1v2"},
            "evidence_status": p2k["formal_status"],
            "outcome_valid": True,
            "route_qualified": False,
            "final_performance_ratio_to_fastest": p2k["replicated_aggregates"]["proposed_final_ratio_to_fastest"],
            "worker_saving_fraction": p2k["replicated_aggregates"]["worker_saving_fraction"],
            "e2e_saving_fraction": p2k["replicated_aggregates"]["worker_saving_fraction"],
            "acquisition_tokens": p2k["economics"]["combined_acquisition_tokens"],
            "break_even_deployments": None,
            "net_tokens_at_8_deployments": None,
            "disqualification": "replicated final performance and second-pair noise fail",
            "source": p2k_source,
        },
        {
            "experiment": "P2l",
            "task_family": "keyed_distinct_energy",
            "workflow": "replicated prepared-representation Profile triplet",
            "route": {"stage-S": "e1v3"},
            "evidence_status": p2l["formal_status"],
            "outcome_valid": True,
            "route_qualified": False,
            "final_performance_ratio_to_fastest": p2l["replicated_aggregates"]["e1v3_performance_ratio_to_neutral"],
            "worker_saving_fraction": p2l["replicated_aggregates"]["e1v3_token_saving_fraction_vs_neutral"],
            "e2e_saving_fraction": p2l["replicated_aggregates"]["e1v3_token_saving_fraction_vs_neutral"],
            "acquisition_tokens": p2l["economics"]["combined_acquisition_tokens"],
            "break_even_deployments": None,
            "net_tokens_at_8_deployments": None,
            "disqualification": "per-repetition performance and eight-deployment economics fail",
            "source": p2l_source,
        },
        {
            "experiment": "P2n",
            "task_family": "local_and_shared_partial_subset",
            "workflow": "three-task revised-Profile matrix with one custody exclusion",
            "route": {"keyed-distinct-min": "p000v2", "keyed-distinct-cube-sum": "e1v3", "affine-checksum": "excluded"},
            "evidence_status": p2n["formal_status"],
            "outcome_valid": True,
            "route_qualified": False,
            "final_performance_ratio_to_fastest": 1.0075762655045257,
            "worker_saving_fraction": p2n["partial_two_task_economics"]["saving_fraction"],
            "e2e_saving_fraction": p2n["partial_two_task_economics"]["saving_fraction"],
            "acquisition_tokens": p2n["partial_two_task_economics"]["valid_subset_acquisition_tokens"],
            "break_even_deployments": p2n["partial_two_task_economics"]["break_even_deployments"],
            "net_tokens_at_8_deployments": p2n["partial_two_task_economics"]["net_tokens_at_8_deployments"],
            "disqualification": "direct task excluded by cross-workspace read custody violation",
            "source": p2n_source,
        },
        {
            "experiment": "P2p",
            "task_family": "direct_bitmix",
            "workflow": "custody-confined direct-task triplet",
            "route": {"direct-bitmix": "p000v2"},
            "evidence_status": p2p["formal_status"],
            "outcome_valid": True,
            "route_qualified": True,
            "final_performance_ratio_to_fastest": p2p["profiles"]["p000v2"]["performance_ratio_to_neutral"],
            "worker_saving_fraction": p2p["profiles"]["p000v2"]["token_saving_fraction"],
            "e2e_saving_fraction": p2p["profiles"]["p000v2"]["token_saving_fraction"],
            "acquisition_tokens": p2p["economics"]["acquisition_tokens"],
            "break_even_deployments": p2p["economics"]["break_even_deployments"],
            "net_tokens_at_8_deployments": p2p["economics"]["net_tokens_at_8_deployments"],
            "source": p2p_source,
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

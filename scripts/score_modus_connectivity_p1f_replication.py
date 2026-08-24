#!/usr/bin/env python3
"""Combine the post-outcome third pair with initial Connectivity evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.qualification_economics import (  # noqa: E402
    evaluate_qualification_economics,
)
from score_modus_connectivity_p1f_workers import (  # noqa: E402
    MAXIMUM_RELATIVE_MAD,
    MINIMUM_WORKER_SAVING,
    PERFORMANCE_RATIO_MAXIMUM,
    _aggregate,
    _usage_tokens,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args(argv)

    root = options.run_root.resolve()
    protocol = json.loads(options.protocol.read_text(encoding="utf-8"))
    repo = options.protocol.resolve().parents[1]
    parent_verification = json.loads(
        (repo / protocol["parent_initial"]["manager_verification_path"]).read_text()
    )
    replication = json.loads((root / "manager-verification.json").read_text())
    combined_cells = parent_verification["cells"] + replication["cells"]

    tasks = {}
    for task_name, task in protocol["tasks"].items():
        actions = {}
        for action in task["actions"]:
            entries = [
                cell for cell in combined_cells
                if cell["task"] == task_name and cell["action"] == action
            ]
            actions[action] = _aggregate(entries)
        fastest = min(value["median_seconds"] for value in actions.values())
        for aggregate in actions.values():
            ratio = aggregate["median_seconds"] / fastest
            aggregate["performance_ratio_to_fastest"] = ratio
            aggregate["performance_gate_passed"] = ratio <= PERFORMANCE_RATIO_MAXIMUM
            aggregate["noise_gate_passed"] = (
                aggregate["maximum_steady_relative_mad"] <= MAXIMUM_RELATIVE_MAD
            )
            aggregate["eligible"] = all((
                aggregate["correctness_passed"],
                aggregate["topology_fidelity_passed"],
                aggregate["semantic_mechanism_passed"],
                aggregate["benchmark_and_usage_complete"],
                aggregate["performance_gate_passed"],
                aggregate["noise_gate_passed"],
            ))
        selected = task["selected_action"]
        neutral_tokens = actions["neutral"]["median_total_tokens"]
        saving = 1.0 - actions[selected]["median_total_tokens"] / neutral_tokens
        selected_passed = actions[selected]["eligible"] and saving >= MINIMUM_WORKER_SAVING
        final_action = selected if selected_passed else "neutral"
        eligible = [name for name, value in actions.items() if value["eligible"]]
        oracle = min(eligible, key=lambda name: actions[name]["median_total_tokens"])
        tasks[task_name] = {
            "selected_action": selected,
            "actions": actions,
            "selected_worker_saving_fraction_vs_neutral": saving,
            "selected_action_passed_all_gates": selected_passed,
            "final_action": final_action,
            "constrained_oracle_action": oracle,
            "agent_matches_constrained_oracle": selected == oracle,
            "repetitions_per_action": 3,
        }

    baseline = sum(task["actions"]["neutral"]["median_total_tokens"] for task in tasks.values())
    routed_worker = sum(
        task["actions"][task["final_action"]]["median_total_tokens"]
        for task in tasks.values()
    )
    router_tokens = protocol["parent_router"]["tokens_per_deployment"]
    routed_e2e = routed_worker + router_tokens
    replication_acquisition = sum(
        _usage_tokens(cell["usage"]) for cell in replication["cells"]
        if _usage_tokens(cell.get("usage")) is not None
    )
    total_acquisition = (
        protocol["parent_initial"]["total_acquisition_tokens"]
        + replication_acquisition
    )
    all_gates = all(task["selected_action_passed_all_gates"] for task in tasks.values())
    economics = evaluate_qualification_economics(
        acquisition_tokens=int(round(total_acquisition)),
        baseline_deployment_tokens=int(round(baseline)),
        candidate_deployment_tokens=int(round(routed_e2e)),
        expected_deployments=protocol["expected_future_deployments"],
        correctness_passed=all_gates,
        performance_passed=all_gates,
        evidence_stable=replication.get("status") == "pass",
        minimum_saving_fraction=MINIMUM_WORKER_SAVING,
    )
    report = {
        "schema": "modus-connectivity-p1f-third-pair-score-v1",
        "status": "pass" if replication.get("status") == "pass" else "fail",
        "post_outcome_replication": True,
        "tasks": tasks,
        "router": {
            "actions_by_task": {name: task["selected_action"] for name, task in tasks.items()},
            "matches_constrained_oracle_on_all_tasks": all(
                task["agent_matches_constrained_oracle"] for task in tasks.values()
            ),
            "tokens_per_deployment": router_tokens,
        },
        "deployment": {
            "fixed_neutral_worker_tokens": baseline,
            "routed_worker_tokens": routed_worker,
            "worker_saving_fraction": 1.0 - routed_worker / baseline,
            "routed_e2e_tokens": routed_e2e,
            "e2e_saving_fraction": 1.0 - routed_e2e / baseline,
        },
        "acquisition": {
            "initial_total_tokens": protocol["parent_initial"]["total_acquisition_tokens"],
            "replication_worker_tokens": replication_acquisition,
            "combined_total_tokens": total_acquisition,
        },
        "economics": economics,
        "replicated_route_passed": all_gates,
    }
    options.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "replicated_route_passed": all_gates,
        "matches_oracle": report["router"]["matches_constrained_oracle_on_all_tasks"],
        "e2e_saving_fraction": report["deployment"]["e2e_saving_fraction"],
        "combined_acquisition_tokens": total_acquisition,
        "break_even": economics["break_even_deployments"],
        "decision_at_expected_deployments": economics["decision"],
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

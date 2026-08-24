#!/usr/bin/env python3
"""Score selected Connectivity Workers and Agent Router end-to-end economics."""

from __future__ import annotations

import argparse
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
MINIMUM_WORKER_SAVING = 0.15
MAXIMUM_RELATIVE_MAD = 0.10


def _usage_tokens(usage: dict) -> int | None:
    if not isinstance(usage, dict):
        return None
    if not all(isinstance(usage.get(key), int) for key in ("input_tokens", "output_tokens")):
        return None
    return usage["input_tokens"] + usage["output_tokens"]


def _aggregate(entries: list[dict]) -> dict:
    seconds = [
        entry["benchmark"]["steady_seconds"]
        for entry in entries if entry.get("benchmark") and entry["benchmark"].get("success")
    ]
    tokens = [_usage_tokens(entry.get("usage")) for entry in entries]
    mads = [
        entry["benchmark"].get("steady_relative_median_absolute_deviation")
        for entry in entries if entry.get("benchmark")
    ]
    complete = (
        len(seconds) == len(entries)
        and all(value is not None for value in tokens)
        and all(value is not None for value in mads)
    )
    return {
        "correctness_passed": all(entry["correct"] for entry in entries),
        "topology_fidelity_passed": all(
            entry["topology_fidelity_passed"] for entry in entries
        ),
        "semantic_mechanism_passed": all(
            entry["semantic_mechanism_passed"] for entry in entries
        ),
        "benchmark_and_usage_complete": complete,
        "median_seconds": statistics.median(seconds) if complete else None,
        "median_total_tokens": statistics.median(tokens) if complete else None,
        "maximum_steady_relative_mad": max(mads) if complete else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args(argv)

    root = options.run_root.resolve()
    protocol = json.loads(options.protocol.read_text(encoding="utf-8"))
    verification = json.loads((root / "manager-verification.json").read_text())
    tasks = {}
    for task_name, task in protocol["tasks"].items():
        actions = {}
        for action in task["actions"]:
            entries = [
                cell for cell in verification["cells"]
                if cell["task"] == task_name and cell["action"] == action
            ]
            actions[action] = _aggregate(entries)
        complete_actions = [
            action for action in actions.values()
            if action["benchmark_and_usage_complete"] and action["correctness_passed"]
        ]
        fastest = min(action["median_seconds"] for action in complete_actions)
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
        neutral_tokens = actions["neutral"]["median_total_tokens"]
        selected = task["selected_action"]
        selected_saving = 1.0 - actions[selected]["median_total_tokens"] / neutral_tokens
        selected_passed = actions[selected]["eligible"] and selected_saving >= MINIMUM_WORKER_SAVING
        final_action = selected if selected_passed else "neutral"
        eligible = [name for name, value in actions.items() if value["eligible"]]
        oracle = min(eligible, key=lambda name: actions[name]["median_total_tokens"])
        tasks[task_name] = {
            "selected_action": selected,
            "actions": actions,
            "selected_worker_saving_fraction_vs_neutral": selected_saving,
            "selected_action_passed_all_gates": selected_passed,
            "final_action": final_action,
            "constrained_oracle_action": oracle,
            "agent_matches_constrained_oracle": selected == oracle,
        }

    baseline_worker_tokens = sum(
        task["actions"]["neutral"]["median_total_tokens"] for task in tasks.values()
    )
    routed_worker_tokens = sum(
        task["actions"][task["final_action"]]["median_total_tokens"]
        for task in tasks.values()
    )
    router = protocol["parent_router"]
    routed_e2e_tokens = routed_worker_tokens + router["tokens_per_deployment"]
    worker_saving = 1.0 - routed_worker_tokens / baseline_worker_tokens
    e2e_saving = 1.0 - routed_e2e_tokens / baseline_worker_tokens
    worker_acquisition = sum(
        _usage_tokens(cell["usage"]) for cell in verification["cells"]
        if _usage_tokens(cell.get("usage")) is not None
    )
    total_acquisition = router["acquisition_tokens"] + worker_acquisition
    all_route_gates = all(task["selected_action_passed_all_gates"] for task in tasks.values())
    economics = evaluate_qualification_economics(
        acquisition_tokens=int(round(total_acquisition)),
        baseline_deployment_tokens=int(round(baseline_worker_tokens)),
        candidate_deployment_tokens=int(round(routed_e2e_tokens)),
        expected_deployments=protocol["expected_future_deployments"],
        correctness_passed=all_route_gates,
        performance_passed=all_route_gates,
        evidence_stable=verification.get("status") == "pass",
        minimum_saving_fraction=MINIMUM_WORKER_SAVING,
    )
    report = {
        "schema": "modus-connectivity-p1f-selected-worker-score-v1",
        "status": "pass" if verification.get("status") == "pass" else "fail",
        "tasks": tasks,
        "router": {
            "actions_by_task": {
                task: value["selected_action"] for task, value in tasks.items()
            },
            "matches_constrained_oracle_on_all_tasks": all(
                task["agent_matches_constrained_oracle"] for task in tasks.values()
            ),
            "tokens_per_deployment": router["tokens_per_deployment"],
        },
        "deployment": {
            "fixed_neutral_worker_tokens": baseline_worker_tokens,
            "routed_worker_tokens": routed_worker_tokens,
            "routed_worker_saving_fraction": worker_saving,
            "routed_e2e_tokens_including_live_router": routed_e2e_tokens,
            "routed_e2e_saving_fraction": e2e_saving,
        },
        "acquisition": {
            "router_tokens": router["acquisition_tokens"],
            "worker_tokens": worker_acquisition,
            "total_tokens": total_acquisition,
        },
        "economics": economics,
        "candidate_qualification": {
            "e1v2_connectivity_y02_passed": tasks["connectivity-y02"]["selected_action_passed_all_gates"],
            "router_live_dispatch_qualified": all_route_gates and economics["decision"] == "promote",
        },
    }
    options.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "actions": report["router"]["actions_by_task"],
        "matches_oracle": report["router"]["matches_constrained_oracle_on_all_tasks"],
        "worker_saving_fraction": worker_saving,
        "e2e_saving_fraction": e2e_saving,
        "acquisition_tokens": total_acquisition,
        "break_even": economics["break_even_deployments"],
        "decision_at_expected_deployments": economics["decision"],
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

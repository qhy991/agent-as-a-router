#!/usr/bin/env python3
"""Score the prospective Reachability wave against the frozen staged gates.

Consumes manager-verification.json plus wave usage, resolves eligibility and
Oracle per task, then recomputes qualification economics with the measured
prospective acquisition cost and compares against the replayed break-even.
"""

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

PERFORMANCE_TOLERANCE = 1.25
TOKEN_TIE = 0.05
MINIMUM_SAVING = 0.15
REPLAYED_STAGED_BREAK_EVEN = 8


def _usage_tokens(usage: dict) -> int | None:
    required = ("input_tokens", "output_tokens")
    if not isinstance(usage, dict) or any(
        not isinstance(usage.get(k), int) for k in required
    ):
        return None
    return usage["input_tokens"] + usage["output_tokens"]


def _median(values: list[float]) -> float:
    return statistics.median(values)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args(argv)

    root = options.run_root.resolve()
    protocol = json.loads(options.protocol.read_text(encoding="utf-8"))
    verification = json.loads(
        (root / "manager-verification.json").read_text(encoding="utf-8")
    )
    by_cell = {cell["cell"]: cell for cell in verification["cells"]}

    tasks_out: dict[str, dict] = {}
    for task_name in protocol["tasks"]:
        actions: dict[str, dict] = {}
        for action in protocol["matrix"]["actions"]:
            entries = [
                by_cell[f"{task_name}-{action}-r{rep}"]
                for rep in range(1, protocol["matrix"]["repetitions_per_action"] + 1)
            ]
            correctness = all(entry["correct"] for entry in entries)
            fidelity = all(entry["topology_fidelity_passed"] for entry in entries)
            tokens = [_usage_tokens(entry["usage"]) for entry in entries]
            usage_complete = all(t is not None for t in tokens)
            seconds = [
                entry["benchmark"]["steady_seconds"]
                for entry in entries
                if entry["benchmark"] and entry["benchmark"].get("success")
            ]
            benchmark_passed = len(seconds) == len(entries)
            actions[action] = {
                "correctness_passed": correctness,
                "behavior_fidelity_passed": fidelity,
                "benchmark_passed": benchmark_passed,
                "usage_complete": usage_complete,
                "median_seconds": _median(seconds) if benchmark_passed else None,
                "median_total_tokens": _median(tokens) if usage_complete else None,
            }
        fastest = min(
            a["median_seconds"]
            for a in actions.values()
            if a["median_seconds"] is not None
        )
        for action, aggregate in actions.items():
            ratio = aggregate["median_seconds"] / fastest
            aggregate["performance_ratio_to_fastest"] = ratio
            aggregate["performance_gate_passed"] = ratio <= 1.0 + PERFORMANCE_TOLERANCE
            aggregate["eligible"] = all((
                aggregate["behavior_fidelity_passed"],
                aggregate["correctness_passed"],
                aggregate["benchmark_passed"],
                aggregate["usage_complete"],
                aggregate["performance_gate_passed"],
            ))
        eligible = [a for a, v in actions.items() if v["eligible"]]
        ordered = sorted(
            eligible,
            key=lambda a: (actions[a]["median_total_tokens"], protocol["matrix"]["actions"].index(a)),
        )
        oracle = None
        if ordered:
            best = actions[ordered[0]]["median_total_tokens"]
            within = [
                a for a in ordered
                if actions[a]["median_total_tokens"] <= best * (1.0 + TOKEN_TIE)
            ]
            oracle = within[0]
        tasks_out[task_name] = {
            "actions": actions,
            "eligible_actions": eligible,
            "oracle_action": oracle,
        }

    fixed_eligible_everywhere = [
        a for a in protocol["matrix"]["actions"]
        if all(tasks_out[t]["actions"][a]["eligible"] for t in tasks_out)
    ]
    fixed_totals = {
        a: sum(tasks_out[t]["actions"][a]["median_total_tokens"] for t in tasks_out)
        for a in fixed_eligible_everywhere
    }
    best_fixed = min(fixed_totals, key=fixed_totals.get) if fixed_totals else None
    oracle_actions = {t: tasks_out[t]["oracle_action"] for t in tasks_out}
    oracle_total = (
        sum(
            tasks_out[t]["actions"][a]["median_total_tokens"]
            for t, a in oracle_actions.items() if a
        )
        if all(oracle_actions.values()) else None
    )
    saving = (
        1.0 - oracle_total / fixed_totals[best_fixed]
        if best_fixed and oracle_total else None
    )
    routing_space = bool(
        saving is not None and saving >= MINIMUM_SAVING
        and len(set(oracle_actions.values())) >= 2
    )

    acquisition = sum(
        _usage_tokens(entry["usage"]) for entry in by_cell.values() if _usage_tokens(entry["usage"])
    )
    economics = None
    default_action = protocol["matrix"]["actions"][0]
    promoted = best_fixed if best_fixed != default_action else None
    if promoted and all(oracle_actions.values()):
        baseline = int(round(fixed_totals[default_action]))
        candidate = int(round(fixed_totals[promoted]))
        acquisition = int(round(acquisition))
        economics = evaluate_qualification_economics(
            acquisition_tokens=acquisition,
            baseline_deployment_tokens=baseline,
            candidate_deployment_tokens=candidate,
            expected_deployments=REPLAYED_STAGED_BREAK_EVEN,
            correctness_passed=all(
                tasks_out[t]["actions"][a]["correctness_passed"]
                for t, a in oracle_actions.items()
            ),
            performance_passed=all(
                tasks_out[t]["actions"][a]["performance_gate_passed"]
                for t, a in oracle_actions.items()
            ),
            evidence_stable=all(
                tasks_out[t]["actions"][a]["behavior_fidelity_passed"]
                for t, a in oracle_actions.items()
            ),
            minimum_saving_fraction=MINIMUM_SAVING,
        )
        economics["comparison"] = (
            f"promotion of fixed {promoted} over the default defer action "
            f"{default_action}; one deployment is one task-pair execution"
        )
        economics["replayed_staged_break_even_deployments"] = REPLAYED_STAGED_BREAK_EVEN
        economics["prospective_replay_break_even_match"] = (
            economics["break_even_deployments"] == REPLAYED_STAGED_BREAK_EVEN
        )

    report = {
        "schema": "modus-reachability-prospective-score-v1",
        "default_defer_action": default_action,
        "promoted_candidate": promoted,
        "tasks": tasks_out,
        "fixed_profiles_eligible_everywhere": fixed_eligible_everywhere,
        "best_fixed_profile": best_fixed,
        "fixed_total_median_tokens": fixed_totals or None,
        "oracle": {
            "actions_by_task": oracle_actions,
            "total_median_tokens": oracle_total,
            "saving_fraction_vs_best_fixed": saving,
        },
        "routing_space": {
            "economic_observed": routing_space,
            "minimum_saving_fraction": MINIMUM_SAVING,
        },
        "prospective_economics": economics,
    }
    options.output.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "oracle_actions": oracle_actions,
        "best_fixed": best_fixed,
        "saving_fraction": saving,
        "routing_space": routing_space,
        "acquisition_tokens": acquisition,
        "break_even": economics["break_even_deployments"] if economics else None,
        "decision": economics["decision"] if economics else None,
        "break_even_matches_replay": (
            economics.get("prospective_replay_break_even_match") if economics else None
        ),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

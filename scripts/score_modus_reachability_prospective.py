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

PERFORMANCE_RATIO_MAXIMUM = 1.25
TOKEN_TIE = 0.05
MINIMUM_SAVING = 0.15
REPLAYED_STAGED_BREAK_EVEN = 8
AMBIGUITY_RATIO_LOWER = PERFORMANCE_RATIO_MAXIMUM * 0.95
AMBIGUITY_RATIO_UPPER = PERFORMANCE_RATIO_MAXIMUM * 1.05
AMBIGUITY_RELATIVE_MAD_MAXIMUM = 0.10


def _usage_tokens(usage: dict) -> int | None:
    required = ("input_tokens", "output_tokens")
    if not isinstance(usage, dict) or any(
        not isinstance(usage.get(k), int) for k in required
    ):
        return None
    return usage["input_tokens"] + usage["output_tokens"]


def _median(values: list[float]) -> float:
    return statistics.median(values)


def _performance_gate(ratio: float) -> bool:
    """Apply the protocol's absolute 1.25x non-inferiority boundary."""
    return ratio <= PERFORMANCE_RATIO_MAXIMUM


def _ambiguity_reasons(
    paired_ratios: list[float], aggregate_ratio: float, relative_mads: list[float]
) -> list[str]:
    reasons = []
    if paired_ratios and min(paired_ratios) <= PERFORMANCE_RATIO_MAXIMUM < max(paired_ratios):
        reasons.append("paired performance ratios straddle 1.25x")
    if AMBIGUITY_RATIO_LOWER <= aggregate_ratio <= AMBIGUITY_RATIO_UPPER:
        reasons.append("aggregate ratio is within five percent of 1.25x")
    if relative_mads and max(relative_mads) > AMBIGUITY_RELATIVE_MAD_MAXIMUM:
        reasons.append("steady relative MAD exceeds 0.10")
    return reasons


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
            aggregate["performance_gate_passed"] = _performance_gate(ratio)
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

        neutral_entries = [
            by_cell[f"{task_name}-neutral-r{rep}"]
            for rep in range(1, protocol["matrix"]["repetitions_per_action"] + 1)
        ]
        p000_entries = [
            by_cell[f"{task_name}-p000-r{rep}"]
            for rep in range(1, protocol["matrix"]["repetitions_per_action"] + 1)
        ]
        paired_ratios = [
            candidate["benchmark"]["steady_seconds"] / baseline["benchmark"]["steady_seconds"]
            for baseline, candidate in zip(neutral_entries, p000_entries)
            if baseline.get("benchmark") and candidate.get("benchmark")
        ]
        aggregate_ratio = actions["p000"]["performance_ratio_to_fastest"]
        relative_mads = [
            entry["benchmark"].get("steady_relative_median_absolute_deviation", 0.0)
            for entry in neutral_entries + p000_entries
            if entry.get("benchmark")
        ]
        ambiguity_reasons = _ambiguity_reasons(
            paired_ratios, aggregate_ratio, relative_mads
        )
        neutral_tokens = actions["neutral"]["median_total_tokens"]
        p000_tokens = actions["p000"]["median_total_tokens"]
        tasks_out[task_name]["p000_saving_fraction_vs_neutral"] = (
            1.0 - p000_tokens / neutral_tokens
            if neutral_tokens and p000_tokens is not None else None
        )
        tasks_out[task_name]["third_pair_trigger"] = {
            "triggered": bool(ambiguity_reasons),
            "reasons": ambiguity_reasons,
            "paired_p000_to_neutral_seconds_ratios": paired_ratios,
            "aggregate_p000_ratio_to_fastest": aggregate_ratio,
            "maximum_steady_relative_mad": max(relative_mads) if relative_mads else None,
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
    ambiguity = any(
        task["third_pair_trigger"]["triggered"] for task in tasks_out.values()
    )
    p000_passed = all(
        task["actions"]["p000"]["eligible"]
        and task["p000_saving_fraction_vs_neutral"] is not None
        and task["p000_saving_fraction_vs_neutral"] >= MINIMUM_SAVING
        for task in tasks_out.values()
    )
    if ambiguity:
        staged_decision = "third_paired_repetition_required"
    elif p000_passed:
        staged_decision = "promote_p000_and_stop"
    else:
        staged_decision = "authorize_p100_follow_up"

    economics = None
    default_action = protocol["matrix"]["actions"][0]
    promoted = best_fixed if best_fixed != default_action else None
    if staged_decision == "promote_p000_and_stop" and promoted == "p000":
        baseline = int(round(fixed_totals[default_action]))
        candidate = int(round(fixed_totals[promoted]))
        acquisition = int(round(acquisition))
        economics = evaluate_qualification_economics(
            acquisition_tokens=acquisition,
            baseline_deployment_tokens=baseline,
            candidate_deployment_tokens=candidate,
            expected_deployments=protocol.get(
                "expected_future_deployments", REPLAYED_STAGED_BREAK_EVEN
            ),
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
        "staged_policy": {
            "decision": staged_decision,
            "p000_passed_all_task_gates": p000_passed,
            "third_pair_triggered": ambiguity,
            "p100_follow_up_authorized": staged_decision == "authorize_p100_follow_up",
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
        "staged_decision": staged_decision,
        "break_even_matches_replay": (
            economics.get("prospective_replay_break_even_match") if economics else None
        ),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Constraint-first offline replay for behavioral Profile routing.

The original ACRouter pipeline treats backend models as actions and may trade
performance against dollar cost.  Profile routing has a stricter scientific
contract: behavior fidelity, correctness, benchmark availability, performance,
and usage completeness are hard gates.  Tokens are compared only after those
gates pass, and one task is assigned exactly one Profile.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any, Callable

from .io_utils import write_json


RESULT_SCHEMA = "acrouter-profile-replay-v1"


class ProfileReplayContractError(ValueError):
    """Raised when a Profile result matrix violates its frozen contract."""


def analyze_profile_file(
    config_path: Path,
    cells_path: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Load, verify, and analyze a fixed-Profile result matrix."""

    config = json.loads(config_path.read_text())
    if config.get("schema") != "acrouter-profile-replay-config-v1":
        raise ProfileReplayContractError("config has the wrong Profile replay schema")
    payload_bytes = cells_path.read_bytes()
    expected_sha = config.get("source", {}).get("cells_sha256")
    observed_sha = hashlib.sha256(payload_bytes).hexdigest()
    if expected_sha and observed_sha != expected_sha:
        raise ProfileReplayContractError(
            f"cells sha256 mismatch: observed {observed_sha}, expected {expected_sha}"
        )
    payload = json.loads(payload_bytes)
    cells = payload.get("cells") if isinstance(payload, dict) else None
    if not isinstance(cells, list):
        raise ProfileReplayContractError("cells input must be an object with a cells list")
    expected_source_schema = config.get("source", {}).get("schema")
    if expected_source_schema and payload.get("schema") != expected_source_schema:
        raise ProfileReplayContractError(
            f"cells schema mismatch: observed {payload.get('schema')!r}, "
            f"expected {expected_source_schema!r}"
        )
    result = analyze_profile_matrix(config, cells)
    result["source"] = {
        "cells_sha256": observed_sha,
        "source_schema": payload.get("schema"),
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        write_json(output_dir / "profile_replay.json", result)
        (output_dir / "summary.md").write_text(render_summary(result))
    return result


def analyze_profile_matrix(
    config: dict[str, Any],
    cells: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute fixed baselines and a constrained per-task Profile Oracle."""

    actions = _string_list(config.get("actions"), "actions")
    tasks = _string_list(config.get("tasks"), "tasks")
    repetitions = _positive_int(config.get("repetitions"), "repetitions")
    profile_specs = config.get("profiles")
    if not isinstance(profile_specs, dict) or set(profile_specs) != set(actions):
        raise ProfileReplayContractError("profiles must define exactly the configured actions")
    tie_order = _string_list(config.get("action_tie_order", actions), "action_tie_order")
    if set(tie_order) != set(actions):
        raise ProfileReplayContractError("action_tie_order must contain every action exactly once")
    tie_rank = {action: index for index, action in enumerate(tie_order)}

    performance = config.get("performance", {})
    metric = str(performance.get("metric", "steady_seconds"))
    if performance.get("lower_is_better", True) is not True:
        raise ProfileReplayContractError("profile replay currently requires a lower-is-better metric")
    tolerance = _nonnegative_number(
        performance.get("eligible_ratio_over_fastest", 0.25),
        "performance.eligible_ratio_over_fastest",
    )
    minimum_saving = _nonnegative_number(
        config.get("minimum_oracle_saving_fraction", 0.15),
        "minimum_oracle_saving_fraction",
    )
    token_equivalence = _fraction(
        config.get("token_equivalence_fraction", 0.0),
        "token_equivalence_fraction",
    )

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    observed_keys: set[tuple[str, str, int]] = set()
    for row in cells:
        task = str(row.get("task") or row.get("task_id") or "")
        action = str(row.get("action") or row.get("profile") or "")
        repetition = row.get("repetition")
        if task not in tasks:
            raise ProfileReplayContractError(f"unexpected task: {task!r}")
        if action not in actions:
            raise ProfileReplayContractError(f"unexpected action: {action!r}")
        if not isinstance(repetition, int) or isinstance(repetition, bool):
            raise ProfileReplayContractError(f"invalid repetition for {task}/{action}")
        key = (task, action, repetition)
        if key in observed_keys:
            raise ProfileReplayContractError(f"duplicate cell: {key}")
        observed_keys.add(key)
        _validate_cell(row, metric)
        grouped[(task, action)].append(row)

    expected_keys = {
        (task, action, repetition)
        for task in tasks
        for action in actions
        for repetition in range(1, repetitions + 1)
    }
    if observed_keys != expected_keys:
        missing = sorted(expected_keys - observed_keys)
        extra = sorted(observed_keys - expected_keys)
        raise ProfileReplayContractError(
            f"fixed matrix mismatch: missing={missing}, extra={extra}"
        )

    task_results: dict[str, Any] = {}
    for task in tasks:
        aggregates: dict[str, Any] = {}
        for action in actions:
            rows = sorted(grouped[(task, action)], key=lambda row: row["repetition"])
            aggregates[action] = _aggregate_action(
                rows,
                metric,
                profile_specs[action],
                repetitions,
            )
        fastest = min(item["median_performance"] for item in aggregates.values())
        for aggregate in aggregates.values():
            ratio = aggregate["median_performance"] / fastest if fastest else 1.0
            aggregate["performance_ratio_to_fastest"] = ratio
            aggregate["performance_gate_passed"] = ratio <= 1.0 + tolerance
            aggregate["eligible"] = all((
                aggregate["behavior_fidelity_passed"],
                aggregate["correctness_passed"],
                aggregate["benchmark_passed"],
                aggregate["usage_complete"],
                aggregate["performance_gate_passed"],
            ))
        eligible_actions = [action for action in actions if aggregates[action]["eligible"]]
        oracle = _choose_action(
            eligible_actions,
            lambda action: aggregates[action]["median_total_tokens"],
            tie_rank,
            token_equivalence,
        )
        task_results[task] = {
            "fastest_median_performance": fastest,
            "eligible_actions": eligible_actions,
            "oracle_action": oracle,
            "actions": aggregates,
        }

    fixed = _fixed_profiles(task_results, actions, tie_rank)
    fixed_eligible = [row for row in fixed if row["all_tasks_eligible"]]
    chosen_fixed = _choose_action(
        [row["profile"] for row in fixed_eligible],
        lambda action: next(
            row["total_median_tokens"] for row in fixed_eligible if row["profile"] == action
        ),
        tie_rank,
        token_equivalence,
    )
    best_fixed = next(
        (row for row in fixed_eligible if row["profile"] == chosen_fixed),
        None,
    )
    oracle_actions = {task: task_results[task]["oracle_action"] for task in tasks}
    oracle_complete = all(action is not None for action in oracle_actions.values())
    oracle_total = (
        sum(
            task_results[task]["actions"][action]["median_total_tokens"]
            for task, action in oracle_actions.items()
            if action is not None
        )
        if oracle_complete
        else None
    )
    distinct_oracle_actions = sorted(
        {action for action in oracle_actions.values() if action is not None},
        key=tie_rank.get,
    )
    saving = None
    if best_fixed and oracle_total is not None and best_fixed["total_median_tokens"]:
        saving = 1.0 - oracle_total / best_fixed["total_median_tokens"]
    routing_space = bool(
        oracle_complete
        and best_fixed
        and len(distinct_oracle_actions) >= 2
        and saving is not None
        and saving >= minimum_saving
    )

    return {
        "schema": RESULT_SCHEMA,
        "name": config.get("name", "profile_replay"),
        "scientific_evidence": bool(config.get("scientific_evidence", False)),
        "tasks": task_results,
        "fixed_profiles": fixed,
        "best_fixed_profile": best_fixed,
        "oracle": {
            "actions_by_task": oracle_actions,
            "distinct_actions": distinct_oracle_actions,
            "total_median_tokens": oracle_total,
            "saving_fraction_vs_best_fixed": saving,
        },
        "routing_space": {
            "observed": routing_space,
            "minimum_saving_fraction": minimum_saving,
            "requires_at_least_two_oracle_actions": True,
            "token_equivalence_fraction": token_equivalence,
        },
        "claim_status": (
            "profile-routing-space-observed"
            if routing_space
            else "no-profile-routing-space-observed"
        ),
        "claim_boundary": config.get("claim_boundary", "offline fixed-Profile replay only"),
    }


def render_summary(result: dict[str, Any]) -> str:
    """Render a compact human-readable replay summary."""

    lines = [
        "# Behavioral Profile Routing Replay",
        "",
        f"- claim status: `{result['claim_status']}`",
        f"- scientific evidence: `{str(result['scientific_evidence']).lower()}`",
        f"- best fixed Profile: `{(result['best_fixed_profile'] or {}).get('profile')}`",
        f"- Oracle actions: `{result['oracle']['actions_by_task']}`",
        f"- routing space observed: `{str(result['routing_space']['observed']).lower()}`",
        "",
        "| task | Oracle | eligible Profiles |",
        "| --- | --- | --- |",
    ]
    for task, task_result in result["tasks"].items():
        eligible = ", ".join(task_result["eligible_actions"]) or "none"
        lines.append(f"| {task} | {task_result['oracle_action']} | {eligible} |")
    return "\n".join(lines) + "\n"


def _aggregate_action(
    rows: list[dict[str, Any]],
    metric: str,
    profile_spec: dict[str, Any],
    repetitions: int,
) -> dict[str, Any]:
    required_topology = profile_spec.get("required_topology")
    minimum_fidelity = _fraction(
        profile_spec.get("minimum_fidelity_fraction", 1.0),
        "minimum_fidelity_fraction",
    )
    matching = (
        repetitions
        if required_topology in (None, "")
        else sum(row.get("topology") == required_topology for row in rows)
    )
    fidelity_fraction = matching / repetitions
    return {
        "repetitions": repetitions,
        "terminal_counts": dict(sorted(Counter(str(row.get("terminal")) for row in rows).items())),
        "correct_repetitions": sum(bool(row.get("correct")) for row in rows),
        "correctness_passed": all(bool(row.get("correct")) for row in rows),
        "benchmark_passed": all(_is_positive_number(row.get(metric)) for row in rows),
        "usage_complete": all(_valid_usage(row) for row in rows),
        "required_topology": required_topology,
        "topology_counts": dict(sorted(Counter(str(row.get("topology")) for row in rows).items())),
        "behavior_fidelity_fraction": fidelity_fraction,
        "behavior_fidelity_passed": fidelity_fraction >= minimum_fidelity,
        "median_performance": float(statistics.median(float(row[metric]) for row in rows)),
        "median_new_tokens": _median_number(row["new_tokens"] for row in rows),
        "median_cache_read_tokens": _median_number(row["cache_read_tokens"] for row in rows),
        "median_total_tokens": _median_number(row["total_tokens"] for row in rows),
    }


def _fixed_profiles(
    task_results: dict[str, Any],
    actions: list[str],
    tie_rank: dict[str, int],
) -> list[dict[str, Any]]:
    rows = []
    for action in actions:
        eligible_tasks = [
            task for task, result in task_results.items()
            if result["actions"][action]["eligible"]
        ]
        all_tasks_eligible = len(eligible_tasks) == len(task_results)
        rows.append({
            "profile": action,
            "all_tasks_eligible": all_tasks_eligible,
            "eligible_tasks": eligible_tasks,
            "total_median_tokens": (
                sum(result["actions"][action]["median_total_tokens"] for result in task_results.values())
                if all_tasks_eligible
                else None
            ),
        })
    return sorted(
        rows,
        key=lambda row: (
            not row["all_tasks_eligible"],
            row["total_median_tokens"] if row["total_median_tokens"] is not None else float("inf"),
            tie_rank[row["profile"]],
        ),
    )


def _choose_action(
    actions: list[str],
    token_value: Callable[[str], int | float],
    tie_rank: dict[str, int],
    equivalence_fraction: float,
) -> str | None:
    if not actions:
        return None
    minimum = min(float(token_value(action)) for action in actions)
    equivalent = [
        action for action in actions
        if float(token_value(action)) <= minimum * (1.0 + equivalence_fraction)
    ]
    return min(equivalent, key=tie_rank.get)


def _median_number(values: Any) -> int | float:
    median = statistics.median(values)
    return int(median) if float(median).is_integer() else float(median)


def _validate_cell(row: dict[str, Any], metric: str) -> None:
    if not _is_positive_number(row.get(metric)):
        raise ProfileReplayContractError(f"cell has invalid {metric}: {row.get('cell_id')}")
    if not _valid_usage(row):
        raise ProfileReplayContractError(f"cell has invalid token usage: {row.get('cell_id')}")
    if not isinstance(row.get("correct"), bool):
        raise ProfileReplayContractError(f"cell has invalid correctness: {row.get('cell_id')}")


def _valid_usage(row: dict[str, Any]) -> bool:
    fields = (row.get("new_tokens"), row.get("cache_read_tokens"), row.get("total_tokens"))
    if not all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in fields):
        return False
    return row["total_tokens"] == row["new_tokens"] + row["cache_read_tokens"]


def _is_nonnegative_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and value >= 0
    )


def _is_positive_number(value: Any) -> bool:
    return _is_nonnegative_number(value) and value > 0


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ProfileReplayContractError(f"{field} must be a non-empty string list")
    if len(set(value)) != len(value):
        raise ProfileReplayContractError(f"{field} contains duplicates")
    return list(value)


def _positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ProfileReplayContractError(f"{field} must be a positive integer")
    return value


def _nonnegative_number(value: Any, field: str) -> float:
    if not _is_nonnegative_number(value):
        raise ProfileReplayContractError(f"{field} must be non-negative")
    return float(value)


def _fraction(value: Any, field: str) -> float:
    result = _nonnegative_number(value, field)
    if result > 1:
        raise ProfileReplayContractError(f"{field} must be at most one")
    return result

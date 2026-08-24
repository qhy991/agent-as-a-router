#!/usr/bin/env python3
"""Fail-closed verifier for the P1e experimental E1-v2 calibration.

Validates each cell workspace against the frozen protocol: hidden-case
correctness, nine-round benchmark timing, exact edit topology, and a dynamic
prepared-representation gate for the experimental E1-v2 candidate.
The frozen verifier treated P1e's legacy Python-dict benchmark line as JSON,
ran seven rather than the protocol's nine manager rounds, and omitted benchmark
success from its aggregate status. This implementation preserves every frozen
scientific gate while correcting those fail-closed implementation defects. It
writes manager-verification.json beside the development calibration wave.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

HIDDEN_EDGES = (
    (0, 1), (1, 2), (2, 0), (2, 4), (4, 5), (5, 6),
    (7, 8), (8, 9), (9, 7),
)
HIDDEN_QUERIES = (
    (0, 6), (6, 0), (4, 6), (5, 4), (7, 9),
    (9, 8), (8, 7), (3, 3), (10, 10), (10, 0),
)
HIDDEN_EXPECTED = (True, False, True, False, True, True, True, True, True, False)

IMPLEMENTATION_FILES = ("api.py", "observer.py", "shared.py", "target.py")


def _hidden_program(package: str) -> str:
    return (
        "from {package}.api import execute\n"
        "edges = {edges}\n"
        "queries = {queries}\n"
        "expected = {expected}\n"
        "result = execute(edges, (queries,))[0]\n"
        "assert result == expected, (result, expected)\n"
        "print('hidden-ok')\n"
    ).format(
        package=package,
        edges=repr(HIDDEN_EDGES),
        queries=repr(HIDDEN_QUERIES),
        expected=repr(list(HIDDEN_EXPECTED)),
    )


def _run(command: list[str], cwd: Path, timeout: int) -> dict:
    try:
        done = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return {
            "returncode": done.returncode,
            "stdout": done.stdout[-4000:],
            "stderr": done.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {"returncode": None, "stdout": "", "stderr": "", "timed_out": True}


def _correctness(workspace: Path, task_id: str, package: str, python: str) -> dict:
    public = _run([python, "-m", "unittest", "discover", "-s", "tests", "-v"],
                  workspace, 120)
    hidden = _run([python, "-c", _hidden_program(package)], workspace, 120)
    return {
        "schema": "modus-performance-p0-correctness-v1",
        "task_id": task_id,
        "public_passed": public["returncode"] == 0,
        "hidden_passed": hidden["returncode"] == 0 and "hidden-ok" in hidden["stdout"],
        "public": public,
        "hidden": hidden,
        "success": public["returncode"] == 0
        and hidden["returncode"] == 0
        and "hidden-ok" in hidden["stdout"],
    }


def _mechanism(workspace: Path, package: str, python: str) -> dict:
    program = (
        "from {package} import observer, target\n"
        "edges = ((0, 1), (1, 2), (2, 0), (2, 4), (4, 5), (5, 6))\n"
        "queries = ((0, 6), (6, 0), (4, 6), (3, 3))\n"
        "prepared = observer.prepare_input(edges)\n"
        "assert prepared is not edges, 'observer returned the raw input object'\n"
        "assert prepared != edges, 'observer preserved the raw edge representation'\n"
        "assert target.answer(prepared, queries) == [True, False, True, True]\n"
        "print('mechanism-ok')\n"
    ).format(package=package)
    result = _run([python, "-c", program], workspace, 120)
    return {
        "schema": "modus-prepared-representation-mechanism-v1",
        "success": result["returncode"] == 0 and "mechanism-ok" in result["stdout"],
        "run": result,
    }


def _parse_benchmark_output(stdout: str) -> dict:
    text = stdout.strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        line = text.splitlines()[-1]
        payload = ast.literal_eval(line)
    if not isinstance(payload, dict):
        raise ValueError("benchmark output is not an object")
    return payload


def _benchmark(workspace: Path, python: str) -> dict:
    rounds = []
    for attempt in range(9):
        done = _run([python, "benchmark.py"], workspace, 300)
        if done["returncode"] != 0:
            return {"schema": "modus-performance-p0-benchmark-v1", "success": False}
        try:
            payload = _parse_benchmark_output(done["stdout"])
            if "steady_seconds" in payload:
                required = {
                    "rounds", "steady_seconds",
                    "steady_relative_median_absolute_deviation", "result_sha256",
                }
                if not required <= set(payload) or payload["rounds"] != 9:
                    return {"schema": "modus-performance-p0-benchmark-v1", "success": False}
                return {**payload, "success": True}
            value = float(payload["seconds"])
        except (ValueError, SyntaxError, KeyError, IndexError, TypeError):
            return {"schema": "modus-performance-p0-benchmark-v1", "success": False}
        rounds.append(value)
    steady = sorted(rounds)[:4]
    steady_seconds = statistics.median(steady)
    steady_mad = statistics.median(abs(value - steady_seconds) for value in steady)
    return {
        "schema": "modus-performance-p0-benchmark-v1",
        "rounds": len(rounds),
        "median_seconds": statistics.median(rounds),
        "steady_seconds": steady_seconds,
        "steady_relative_median_absolute_deviation": (
            steady_mad / steady_seconds if steady_seconds else 0.0
        ),
        "all_seconds": rounds,
        "success": True,
    }


def _topology(workspace: Path, task_id: str, package: str, seed: Path, expected: str) -> dict:
    changed = []
    for name in IMPLEMENTATION_FILES:
        current = workspace / package / name
        origin = seed / package / name
        if not current.is_file():
            changed.append(f"{package}/{name}")
        elif hashlib.sha256(current.read_bytes()).hexdigest() != \
                hashlib.sha256(origin.read_bytes()).hexdigest():
            changed.append(f"{package}/{name}")
    if expected == "local":
        topology = "local" if changed == [f"{package}/target.py"] else "violated"
    elif expected == "coordinated":
        coordinated = [
            f"{package}/observer.py",
            f"{package}/shared.py",
            f"{package}/target.py",
        ]
        topology = "coordinated" if changed == coordinated else "violated"
    elif expected == "unconstrained":
        topology = "unconstrained" if changed else "seed-unchanged"
    else:
        topology = "unknown-expectation"
    return {
        "schema": "modus-performance-p0-topology-v1",
        "task_id": task_id,
        "changed_implementation_paths": changed,
        "expected_topology": expected,
        "topology": topology,
        "passed": topology in {"local", "coordinated", "unconstrained"},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument(
        "--python",
        default="/Users/haiyan-infiniai/.cache/codex-runtimes/"
        "codex-primary-runtime/dependencies/python/bin/python",
    )
    options = parser.parse_args(argv)

    root = options.run_root.resolve()
    protocol = json.loads(options.protocol.read_text(encoding="utf-8"))
    repo = options.protocol.resolve().parents[1]

    result = json.loads((root / "output" / "wave-result.json").read_text())
    usage_by_cell = {
        cell["cell"]: cell.get("usage") for cell in result["cells"]
    }
    valid_by_cell = {
        cell["cell"]: cell["valid_execution"] for cell in result["cells"]
    }

    cells = []
    for task_name, task in protocol["tasks"].items():
        seed = repo / task["seed_root"]
        package = task.get("package", task_name.replace("reachability-", "perf_reachability_"))
        task_id = task["task_id"]
        for action in protocol["matrix"]["actions"]:
            for rep in range(1, protocol["matrix"]["repetitions_per_action"] + 1):
                cell_id = f"{task_name}-{action}-r{rep}"
                workspace = root / "workspaces" / cell_id
                expected = {
                    "p000": "local",
                    "p100": "coordinated",
                    "e1v2": "coordinated",
                }.get(action, "unconstrained")
                entry = {
                    "cell": cell_id,
                    "action": action,
                    "task": task_name,
                    "repetition": rep,
                    "wave_valid_execution": valid_by_cell.get(cell_id),
                    "usage": usage_by_cell.get(cell_id),
                    "usage_complete": usage_by_cell.get(cell_id) is not None,
                }
                if not entry["wave_valid_execution"]:
                    entry["correct"] = False
                    entry["correctness"] = None
                    entry["benchmark"] = None
                    entry["topology"] = None
                    entry["topology_fidelity_passed"] = False
                    entry["semantic_mechanism"] = None
                    entry["semantic_mechanism_required"] = action == "e1v2"
                    entry["semantic_mechanism_passed"] = False
                else:
                    correctness = _correctness(workspace, task_id, package, options.python)
                    benchmark = _benchmark(workspace, options.python)
                    topology = _topology(workspace, task_id, package, seed, expected)
                    entry["correctness"] = correctness
                    entry["benchmark"] = benchmark
                    entry["topology"] = topology
                    entry["correct"] = correctness["success"]
                    entry["topology_fidelity_passed"] = topology["passed"]
                    entry["semantic_mechanism_required"] = action == "e1v2"
                    if action == "e1v2":
                        mechanism = _mechanism(workspace, package, options.python)
                        entry["semantic_mechanism"] = mechanism
                        entry["semantic_mechanism_passed"] = mechanism["success"]
                    else:
                        entry["semantic_mechanism"] = None
                        entry["semantic_mechanism_passed"] = True
                cells.append(entry)

    correct = sum(1 for c in cells if c["correct"])
    fidelity = sum(1 for c in cells if c["topology_fidelity_passed"])
    usage_complete = sum(1 for c in cells if c["usage_complete"])
    benchmarked = sum(
        1 for c in cells if c["benchmark"] and c["benchmark"].get("success")
    )
    semantic_required = sum(c["semantic_mechanism_required"] for c in cells)
    semantic_passed = sum(
        c["semantic_mechanism_required"] and c["semantic_mechanism_passed"]
        for c in cells
    )
    verification = {
        "schema": "modus-reachability-p1e-e1v2-calibration-verification-v1",
        "measurement_dispatch": "sequential",
        "cells": cells,
        "correct_cells": correct,
        "topology_fidelity_cells": fidelity,
        "usage_complete_cells": usage_complete,
        "benchmarked_cells": benchmarked,
        "semantic_mechanism_required_cells": semantic_required,
        "semantic_mechanism_passed_cells": semantic_passed,
        "status": "pass" if (
            correct == len(cells) == fidelity == usage_complete == benchmarked
            and semantic_required == semantic_passed
        )
        else "fail",
    }
    destination = root / "manager-verification.json"
    destination.write_text(json.dumps(verification, indent=1, sort_keys=True))
    print(json.dumps({
        "status": verification["status"],
        "cells": len(cells),
        "correct": correct,
        "topology_fidelity": fidelity,
        "usage_complete": usage_complete,
        "benchmarked": benchmarked,
        "semantic_required": semantic_required,
        "semantic_passed": semantic_passed,
    }, sort_keys=True))
    return 0 if verification["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

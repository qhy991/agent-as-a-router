#!/usr/bin/env python3
"""Fail-closed verifier for the prospective Reachability neutral/p000 wave.

Validates each cell workspace against the frozen protocol: hidden-case
correctness, steady-state benchmark timing, and local-only topology for p000.
Writes manager-verification.json beside the wave result.
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

HIDDEN_CASES = {
    "reachability-p03": [
        (0, 1), (1, 0), (0, 0), (5, 5),
        (0, 639), (639, 0), (319, 320), (320, 319),
        (638, 637), (4, 65), (65, 4), (16, 19),
    ],
    "reachability-p04": [
        (0, 1), (1, 0), (0, 0), (5, 5),
        (0, 639), (639, 0), (319, 320), (320, 319),
        (638, 637), (4, 65), (65, 4), (16, 19),
    ],
}

IMPLEMENTATION_FILES = ("api.py", "observer.py", "shared.py", "target.py")


def _hidden_program(task: str) -> str:
    cases = HIDDEN_CASES[task]
    return (
        "from perf_{pkg}.api import execute\n"
        "nodes = 640\n"
        "edges = [(i, (i + 1) % nodes) for i in range(nodes)]\n"
        "edges.extend((i, (i + 61) % nodes) for i in range(0, nodes, 4))\n"
        "edges.extend(((i + 3) % nodes, i) for i in range(0, nodes, 16))\n"
        "queries = {cases}\n"
        "expected = [True] * len(queries)\n"
        "result = execute(tuple(edges), (queries,))[0]\n"
        "assert result == expected, (result, expected)\n"
        "print('hidden-ok')\n"
    ).format(pkg=task.replace("reachability-", "reachability_"), cases=repr(tuple(cases)))


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


def _correctness(workspace: Path, task: str, python: str) -> dict:
    public = _run([python, "-m", "unittest", "discover", "-s", "tests", "-v"],
                  workspace, 120)
    hidden = _run([python, "-c", _hidden_program(task)], workspace, 120)
    return {
        "schema": "modus-performance-p0-correctness-v1",
        "task_id": f"{task}-perf-p0",
        "public_passed": public["returncode"] == 0,
        "hidden_passed": hidden["returncode"] == 0 and "hidden-ok" in hidden["stdout"],
        "public": public,
        "hidden": hidden,
        "success": public["returncode"] == 0
        and hidden["returncode"] == 0
        and "hidden-ok" in hidden["stdout"],
    }


def _benchmark(workspace: Path, python: str) -> dict:
    rounds = []
    for _ in range(7):
        done = _run([python, "benchmark.py"], workspace, 300)
        if done["returncode"] != 0:
            return {"schema": "modus-performance-p0-benchmark-v1", "success": False}
        try:
            line = done["stdout"].strip().splitlines()[-1]
            value = float(ast.literal_eval(line)["seconds"])
        except (ValueError, SyntaxError, KeyError, IndexError, TypeError):
            return {"schema": "modus-performance-p0-benchmark-v1", "success": False}
        rounds.append(value)
    steady = sorted(rounds)[:3]
    return {
        "schema": "modus-performance-p0-benchmark-v1",
        "rounds": len(rounds),
        "median_seconds": statistics.median(rounds),
        "steady_seconds": statistics.median(steady),
        "all_seconds": rounds,
        "success": True,
    }


def _topology(workspace: Path, task: str, seed: Path, expected: str) -> dict:
    package = task.replace("reachability-", "perf_reachability_")
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
    elif expected == "unconstrained":
        topology = "unconstrained" if changed else "seed-unchanged"
    else:
        topology = "unknown-expectation"
    return {
        "schema": "modus-performance-p0-topology-v1",
        "task_id": task,
        "changed_implementation_paths": changed,
        "expected_topology": expected,
        "topology": topology,
        "passed": topology in {"local", "unconstrained"},
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
        for action in protocol["matrix"]["actions"]:
            for rep in range(1, protocol["matrix"]["repetitions_per_action"] + 1):
                cell_id = f"{task_name}-{action}-r{rep}"
                workspace = root / "workspaces" / cell_id
                expected = (
                    "local" if action == "p000" else "unconstrained"
                )
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
                else:
                    correctness = _correctness(workspace, task_name, options.python)
                    benchmark = _benchmark(workspace, options.python)
                    topology = _topology(workspace, task_name, seed, expected)
                    entry["correctness"] = correctness
                    entry["benchmark"] = benchmark
                    entry["topology"] = topology
                    entry["correct"] = correctness["success"]
                    entry["topology_fidelity_passed"] = topology["passed"]
                cells.append(entry)

    correct = sum(1 for c in cells if c["correct"])
    fidelity = sum(1 for c in cells if c["topology_fidelity_passed"])
    usage_complete = sum(1 for c in cells if c["usage_complete"])
    verification = {
        "schema": "modus-reachability-prospective-verification-v1",
        "measurement_dispatch": "sequential",
        "cells": cells,
        "correct_cells": correct,
        "topology_fidelity_cells": fidelity,
        "usage_complete_cells": usage_complete,
        "status": "pass" if correct == len(cells) == fidelity == usage_complete
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
    }, sort_keys=True))
    return 0 if verification["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify one invariant-specialization manipulation cell."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import statistics
import subprocess
from pathlib import Path


TASKS = {
    "modular-bit-transform": {
        "package": "modus_invariant_modular_bit_transform",
        "data": (3, 7, 11, 3, 101),
        "queries": (-3, 0, 8, 99),
        "expected": [83, 80, 77, 5],
        "forbidden": ("rotation %=", "multiplier %=", "offset %="),
    },
    "rolling-hash": {
        "package": "modus_invariant_rolling_hash",
        "data": (17, 11, 257),
        "queries": ((0, 255), (3, 4, 5)),
        "expected": [174, 11],
        "forbidden": ("range(256)", "salt &=", "base %="),
    },
    "polynomial-transform": {
        "package": "modus_invariant_polynomial_transform",
        "data": ((7, -2, 9, 4), 101),
        "queries": (-1, 0, 5),
        "expected": [87, 4, 66],
        "forbidden": ("coefficient % modulus for coefficient",),
    },
    "crc-transform": {
        "package": "modus_invariant_crc_transform",
        "data": (29, 255, 85),
        "queries": ((0, 1), (3, 5, 8)),
        "expected": [9, 94],
        "forbidden": ("range(256)", "range(8)", "def _table"),
    },
}
STRATEGIES = (
    "target-scoped-optimization",
    "prepared-shared-optimization",
    "invariant-specialized-optimization",
)
IMPLEMENTATION_FILES = ("api.py", "observer.py", "shared.py", "target.py")
FROZEN_FILES = (".modus-task.json", "benchmark.py", "instruction.md", "tests/test_public.py")
INDEX_MARKERS = ("defaultdict", "Counter(", "setdefault(", "dict[")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path, timeout: int = 300) -> dict:
    try:
        done = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return {
            "returncode": done.returncode,
            "stdout": done.stdout[-4000:],
            "stderr": done.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {"returncode": None, "stdout": "", "stderr": "", "timed_out": True}


def observer_calls_shared(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.FunctionDef) and node.name == "prepare_input":
            return any(isinstance(item, ast.Call) for item in ast.walk(node))
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--task", choices=tuple(TASKS), required=True)
    parser.add_argument("--strategy", choices=STRATEGIES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", required=True)
    args = parser.parse_args(argv)
    workspace = args.workspace.resolve()
    seed = args.seed.resolve()
    spec = TASKS[args.task]
    package = spec["package"]
    public = run(
        [args.python, "-m", "unittest", "discover", "-s", "tests", "-v"],
        workspace,
        120,
    )
    hidden_program = (
        f"from {package}.api import execute\n"
        f"data={spec['data']!r}\nqueries={spec['queries']!r}\n"
        f"expected={spec['expected']!r}\n"
        "result=execute(data,(queries,))[0]\n"
        "assert result==expected,(result,expected)\nprint('hidden-ok')\n"
    )
    hidden = run([args.python, "-c", hidden_program], workspace, 120)
    correctness = (
        public["returncode"] == hidden["returncode"] == 0
        and "hidden-ok" in hidden["stdout"]
    )
    custody = all(
        (workspace / relative).is_file()
        and sha256(workspace / relative) == sha256(seed / relative)
        for relative in FROZEN_FILES
    )
    changed = [
        f"{package}/{name}"
        for name in IMPLEMENTATION_FILES
        if not (workspace / package / name).is_file()
        or sha256(workspace / package / name) != sha256(seed / package / name)
    ]
    expected_changed = (
        [f"{package}/target.py"]
        if args.strategy == "target-scoped-optimization"
        else sorted([
            f"{package}/observer.py",
            f"{package}/shared.py",
            f"{package}/target.py",
        ])
    )
    topology = changed == expected_changed
    invariant_required = args.strategy == "invariant-specialized-optimization"
    observer_source = (workspace / package / "observer.py").read_text()
    shared_source = (workspace / package / "shared.py").read_text()
    target_source = (workspace / package / "target.py").read_text()
    api_source = (workspace / package / "api.py").read_text()
    mechanism_runtime = None
    if invariant_required:
        mechanism_program = (
            f"from {package} import observer,target\n"
            f"data={spec['data']!r}\nqueries={spec['queries']!r}\n"
            f"expected={spec['expected']!r}\n"
            "prepared=observer.prepare_input(data)\n"
            "assert prepared is not data\n"
            "assert len(repr(prepared)) < 20000\n"
            "result=target.answer(prepared,queries)\n"
            "assert result==expected,(result,expected)\n"
            "print('invariant-mechanism-ok')\n"
        )
        mechanism_runtime = run([args.python, "-c", mechanism_program], workspace, 120)
        runtime_ok = (
            mechanism_runtime["returncode"] == 0
            and "invariant-mechanism-ok" in mechanism_runtime["stdout"]
        )
        shared_helper = any(
            isinstance(node, ast.FunctionDef)
            for node in ast.parse(shared_source).body
        )
        observer_shared = observer_calls_shared(observer_source)
        target_clean = all(fragment not in target_source for fragment in spec["forbidden"])
        no_data_index = all(marker not in shared_source for marker in INDEX_MARKERS)
        preparation_once = (
            api_source.count("observer.prepare_input") == 1
            and sha256(workspace / package / "api.py") == sha256(seed / package / "api.py")
        )
    else:
        runtime_ok = shared_helper = observer_shared = target_clean = no_data_index = preparation_once = True
    behavior = {
        "topology_exact": topology,
        "runtime_prepared_semantics": runtime_ok,
        "shared_specialization_helper": shared_helper,
        "observer_invokes_shared_preparation": observer_shared,
        "target_invariants_absent": target_clean,
        "no_data_dependent_index": no_data_index,
        "preparation_once": preparation_once,
    }
    behavior_core = all(
        value for key, value in behavior.items()
        if key != "target_invariants_absent"
    )
    samples = []
    failed_run = None
    for _ in range(15):
        result = run([args.python, "benchmark.py"], workspace, 300)
        if result["returncode"] != 0:
            failed_run = result
            break
        try:
            raw = result["stdout"].strip()
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                value = ast.literal_eval(raw.splitlines()[-1])
            samples.append(float(value["seconds"]))
        except Exception:
            failed_run = result
            break
    if len(samples) == 15:
        steady_samples = sorted(samples)[:7]
        seconds = statistics.median(steady_samples)
        relative_mad = (
            statistics.median(abs(sample - seconds) for sample in steady_samples)
            / seconds if seconds else 0.0
        )
        benchmark = True
    else:
        seconds = relative_mad = None
        benchmark = False
    checks = {
        "custody": custody,
        "correctness": correctness,
        "behavior_core": behavior_core,
        "benchmark": benchmark,
    }
    digest = hashlib.sha256()
    for path in sorted((workspace / package).glob("*.py")):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    report = {
        "schema": "modus-invariant-specialization-cell-verification-v1",
        "task_id": args.task,
        "strategy": args.strategy,
        "checks": checks,
        "passed": all(checks.values()),
        "behavior": behavior,
        "implementation_digest": digest.hexdigest(),
        "changed_implementation_paths": changed,
        "correctness": {"public": public, "hidden": hidden},
        "mechanism_runtime": mechanism_runtime,
        "benchmark": {
            "success": benchmark,
            "rounds": len(samples),
            "all_seconds": samples,
            "steady_seconds": seconds,
            "steady_relative_mad": relative_mad,
            "failed_run": failed_run,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "task_id": args.task,
        "strategy": args.strategy,
        "passed": report["passed"],
        "seconds": seconds,
    }, sort_keys=True))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

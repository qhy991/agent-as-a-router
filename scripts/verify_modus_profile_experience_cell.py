#!/usr/bin/env python3
"""Fail-closed verifier for one formal Profile experience transfer cell."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import statistics
import subprocess
from pathlib import Path


TASKS = {
    "single-batch-keyed-reduction": {
        "package": "modus_single_batch_keyed_reduction",
        "data": ((0, 3), (0, -1), (1, 9), (1, 4)),
        "queries": (0, 1, 2, 9),
        "expected": [-1, None, None, None],
    },
    "repeated-batch-keyed-aggregate": {
        "package": "modus_repeated_batch_keyed_aggregate",
        "data": ((0, -1), (0, -1), (0, 2), (1, 3)),
        "queries": (0, 1, 2, 9),
        "expected": [17, 81, 0, 0],
    },
    "direct-bit-transformation": {
        "package": "modus_direct_bit_transformation",
        "data": (3, 7, 11, 3, 101),
        "queries": (-3, 0, 8, 99),
        "expected": [83, 80, 77, 5],
    },
}
STRATEGIES = (
    "unconstrained-optimization",
    "target-scoped-optimization",
    "prepared-shared-optimization",
)
IMPLEMENTATION_FILES = ("api.py", "observer.py", "shared.py", "target.py")
FROZEN_FILES = (".modus-task.json", "benchmark.py", "instruction.md", "tests/test_public.py")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str], cwd: Path, timeout: int = 300) -> dict:
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
        return {
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timed_out": True,
        }


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
    public = _run(
        [args.python, "-m", "unittest", "discover", "-s", "tests", "-v"],
        workspace,
        120,
    )
    program = (
        f"from {package}.api import execute\n"
        f"data={spec['data']!r}\nq={spec['queries']!r}\n"
        f"expected={spec['expected']!r}\n"
        "result=execute(data,(q,))[0]\n"
        "assert result==expected,(result,expected)\nprint('hidden-ok')\n"
    )
    hidden = _run([args.python, "-c", program], workspace, 120)
    correctness = (
        public["returncode"] == hidden["returncode"] == 0
        and "hidden-ok" in hidden["stdout"]
    )
    custody = all(
        (workspace / relative).is_file()
        and _sha(workspace / relative) == _sha(seed / relative)
        for relative in FROZEN_FILES
    )
    changed = [
        f"{package}/{name}"
        for name in IMPLEMENTATION_FILES
        if not (workspace / package / name).is_file()
        or _sha(workspace / package / name) != _sha(seed / package / name)
    ]
    wanted = {
        "unconstrained-optimization": None,
        "target-scoped-optimization": [f"{package}/target.py"],
        "prepared-shared-optimization": [
            f"{package}/observer.py",
            f"{package}/shared.py",
            f"{package}/target.py",
        ],
    }[args.strategy]
    topology = True if wanted is None else changed == wanted
    mechanism = None
    if args.strategy == "prepared-shared-optimization":
        mechanism_program = (
            f"from {package} import observer,target\n"
            f"data={spec['data']!r}\nq={spec['queries']!r}\n"
            f"expected={spec['expected']!r}\n"
            "prepared=observer.prepare_input(data)\n"
            "assert prepared is not data\n"
            "assert target.answer(prepared,q)==expected\n"
            "print('mechanism-ok')\n"
        )
        mechanism = _run([args.python, "-c", mechanism_program], workspace, 120)
        mechanism_ok = (
            mechanism["returncode"] == 0
            and "mechanism-ok" in mechanism["stdout"]
        )
    else:
        mechanism_ok = True
    samples = []
    failed_run = None
    for _ in range(15):
        result = _run([args.python, "benchmark.py"], workspace, 300)
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
        steady = sorted(samples)[:7]
        seconds = statistics.median(steady)
        relative_mad = (
            statistics.median(abs(item - seconds) for item in steady) / seconds
            if seconds else 0.0
        )
        benchmark = True
    else:
        seconds = None
        relative_mad = None
        benchmark = False
    checks = {
        "custody": custody,
        "correctness": correctness,
        "topology": topology,
        "semantic_mechanism": mechanism_ok,
        "benchmark": benchmark,
    }
    digest = hashlib.sha256()
    for path in sorted((workspace / package).glob("*.py")):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    report = {
        "schema": "modus-profile-experience-cell-verification-v1",
        "task_id": args.task,
        "strategy": args.strategy,
        "checks": checks,
        "passed": all(checks.values()),
        "implementation_digest": digest.hexdigest(),
        "changed_implementation_paths": changed,
        "correctness": {"public": public, "hidden": hidden},
        "semantic_mechanism": mechanism,
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

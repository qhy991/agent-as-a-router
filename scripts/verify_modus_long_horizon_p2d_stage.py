#!/usr/bin/env python3
"""Fail-closed manager verifier for one linked P2d Membership stage."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import statistics
import subprocess
from pathlib import Path


PACKAGE = "perf_linked_membership"
IMPLEMENTATION_FILES = ("api.py", "observer.py", "shared.py", "target.py")
FROZEN_FILES = (
    ".modus-task.json", "benchmark_stage_l.py", "benchmark_final.py",
    "tests/test_public.py",
)
HIDDEN_DATA = (3, 1, 3)
HIDDEN_QUERIES = (1, 2, 3, 4)
HIDDEN_EXPECTED = [True, False, True, False]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _implementation_digest(workspace: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((workspace / PACKAGE).glob("*.py")):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


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


def _correctness(workspace: Path, python: str) -> dict:
    public = _run([python, "-m", "unittest", "discover", "-s", "tests", "-v"], workspace, 120)
    hidden_program = (
        f"from {PACKAGE}.api import execute\n"
        f"data = {HIDDEN_DATA!r}\nqueries = {HIDDEN_QUERIES!r}\n"
        f"expected = {HIDDEN_EXPECTED!r}\n"
        "result = execute(data, (queries,))[0]\n"
        "assert result == expected, (result, expected)\nprint('hidden-ok')\n"
    )
    hidden = _run([python, "-c", hidden_program], workspace, 120)
    return {
        "public": public,
        "hidden": hidden,
        "success": (
            public["returncode"] == 0
            and hidden["returncode"] == 0
            and "hidden-ok" in hidden["stdout"]
        ),
    }


def _custody(workspace: Path, seed: Path) -> dict:
    rows = {}
    for relative in FROZEN_FILES:
        expected = seed / relative
        actual = workspace / relative
        rows[relative] = {
            "present": actual.is_file(),
            "expected_sha256": _sha256(expected),
            "actual_sha256": _sha256(actual) if actual.is_file() else None,
        }
    return {
        "files": rows,
        "passed": all(
            row["present"] and row["actual_sha256"] == row["expected_sha256"]
            for row in rows.values()
        ),
    }


def _topology(workspace: Path, seed: Path, expected: str) -> dict:
    changed = []
    for name in IMPLEMENTATION_FILES:
        current = workspace / PACKAGE / name
        origin = seed / PACKAGE / name
        if not current.is_file() or _sha256(current) != _sha256(origin):
            changed.append(f"{PACKAGE}/{name}")
    if expected == "local":
        topology = "local" if changed == [f"{PACKAGE}/target.py"] else "violated"
    elif expected == "coordinated":
        wanted = [
            f"{PACKAGE}/observer.py", f"{PACKAGE}/shared.py",
            f"{PACKAGE}/target.py",
        ]
        topology = "coordinated" if changed == wanted else "violated"
    else:
        topology = "unconstrained"
    return {
        "changed_implementation_paths": changed,
        "expected_topology": expected,
        "topology": topology,
        "passed": topology in {"local", "coordinated", "unconstrained"},
    }


def _mechanism(workspace: Path, python: str) -> dict:
    program = (
        f"from {PACKAGE} import observer, target\n"
        "data = (3, 1, 3)\n"
        "queries = (1, 2, 3, 4)\n"
        "prepared = observer.prepare_input(data)\n"
        "assert prepared is not data and prepared != data\n"
        "assert target.answer(prepared, queries) == [True, False, True, False]\n"
        "print('mechanism-ok')\n"
    )
    result = _run([python, "-c", program], workspace, 120)
    return {
        "run": result,
        "success": result["returncode"] == 0 and "mechanism-ok" in result["stdout"],
    }


def _parse_benchmark(stdout: str) -> float:
    text = stdout.strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = ast.literal_eval(text.splitlines()[-1])
    return float(value["seconds"])


def _benchmark(workspace: Path, stage: str, python: str) -> dict:
    script = "benchmark_stage_l.py" if stage == "L" else "benchmark_final.py"
    samples = []
    for _ in range(9):
        result = _run([python, script], workspace, 300)
        if result["returncode"] != 0:
            return {"success": False, "samples": samples, "failed_run": result}
        try:
            samples.append(_parse_benchmark(result["stdout"]))
        except (ValueError, SyntaxError, KeyError, TypeError):
            return {"success": False, "samples": samples, "failed_run": result}
    steady = sorted(samples)[:4]
    steady_seconds = statistics.median(steady)
    mad = statistics.median(abs(value - steady_seconds) for value in steady)
    return {
        "success": True,
        "rounds": 9,
        "all_seconds": samples,
        "median_seconds": statistics.median(samples),
        "steady_seconds": steady_seconds,
        "steady_relative_mad": mad / steady_seconds if steady_seconds else 0.0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--stage", choices=("L", "S"), required=True)
    parser.add_argument("--arm", choices=("routed", "neutral"), required=True)
    parser.add_argument("--profile", choices=("neutral", "p000", "e1v2"), required=True)
    parser.add_argument("--parent-record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--python",
        default="/Users/haiyan-infiniai/.cache/codex-runtimes/"
        "codex-primary-runtime/dependencies/python/bin/python",
    )
    args = parser.parse_args(argv)
    workspace, seed = args.workspace.resolve(), args.seed.resolve()
    expected = "unconstrained" if args.arm == "neutral" else "coordinated"
    custody = _custody(workspace, seed)
    correctness = _correctness(workspace, args.python)
    topology = _topology(workspace, seed, expected)
    mechanism_required = args.arm == "routed"
    mechanism = _mechanism(workspace, args.python) if mechanism_required else None
    benchmark = _benchmark(workspace, args.stage, args.python)
    parent = None
    parent_bound = args.stage == "L"
    parent_delta_passed = args.stage == "L" or args.arm == "neutral"
    changed_from_parent = None
    if args.stage == "S" and args.parent_record and args.parent_record.is_file():
        parent = json.loads(args.parent_record.read_text())
        parent_bound = (
            parent.get("schema") == "modus-long-horizon-p2d-parent-v1"
            and isinstance(parent.get("implementation_digest"), str)
            and isinstance(parent.get("stage_l_verification_sha256"), str)
            and isinstance(parent.get("implementation_files_sha256"), dict)
        )
        if args.arm == "routed" and args.profile == "p000" and parent_bound:
            before = parent["implementation_files_sha256"]
            after = {
                path.name: _sha256(path)
                for path in sorted((workspace / PACKAGE).glob("*.py"))
            }
            changed_from_parent = sorted(
                name for name in set(before) | set(after)
                if before.get(name) != after.get(name)
            )
            parent_delta_passed = changed_from_parent == ["target.py"]
    checks = {
        "custody": custody["passed"],
        "correctness": correctness["success"],
        "topology": topology["passed"],
        "semantic_mechanism": not mechanism_required or mechanism["success"],
        "benchmark": benchmark["success"],
        "parent_record": parent_bound,
        "parent_profile_delta": parent_delta_passed,
    }
    report = {
        "schema": "modus-long-horizon-p2d-stage-verification-v1",
        "stage": args.stage,
        "arm": args.arm,
        "profile": args.profile,
        "checks": checks,
        "passed": all(checks.values()),
        "implementation_digest": _implementation_digest(workspace),
        "custody": custody,
        "correctness": correctness,
        "topology": topology,
        "semantic_mechanism": mechanism,
        "benchmark": benchmark,
        "parent_record": parent,
        "changed_from_parent": changed_from_parent,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "passed": report["passed"], "stage": args.stage, "arm": args.arm,
        "profile": args.profile, "seconds": benchmark.get("steady_seconds"),
        "implementation_digest": report["implementation_digest"],
    }, sort_keys=True))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

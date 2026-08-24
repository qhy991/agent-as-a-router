#!/usr/bin/env python3
"""Fail-closed verifier for one P2l keyed-energy Profile cell."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import statistics
import subprocess


PACKAGE = "perf_energy_p2l"
IMPLEMENTATION_FILES = ("api.py", "observer.py", "shared.py", "target.py")
FROZEN_FILES = (
    ".modus-task.json", "benchmark.py", "instruction.md", "tests/test_public.py",
)
HIDDEN_DATA = ((0, -1), (0, -1), (0, 3), (1, 3), (1, 4), (1, 4))
HIDDEN_QUERIES = (0, 1, 2, 9)
HIDDEN_EXPECTED = [10, 25, 0, 0]


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
    public = _run(
        [python, "-m", "unittest", "discover", "-s", "tests", "-v"],
        workspace,
        120,
    )
    hidden_program = (
        f"from {PACKAGE}.api import execute\n"
        f"data = {HIDDEN_DATA!r}\nqueries = {HIDDEN_QUERIES!r}\n"
        f"expected = {HIDDEN_EXPECTED!r}\n"
        "result = execute(data, (queries,))[0]\n"
        "assert result == expected, (result, expected)\n"
        "print('hidden-ok')\n"
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


def _topology(workspace: Path, seed: Path, profile: str) -> dict:
    changed = []
    for name in IMPLEMENTATION_FILES:
        current = workspace / PACKAGE / name
        origin = seed / PACKAGE / name
        if not current.is_file() or _sha256(current) != _sha256(origin):
            changed.append(f"{PACKAGE}/{name}")
    if profile == "neutral":
        topology = "unconstrained"
    else:
        wanted = [
            f"{PACKAGE}/observer.py", f"{PACKAGE}/shared.py", f"{PACKAGE}/target.py",
        ]
        topology = "coordinated" if changed == wanted else "violated"
    return {
        "changed_implementation_paths": changed,
        "expected_topology": "unconstrained" if profile == "neutral" else "coordinated",
        "topology": topology,
        "passed": topology in {"unconstrained", "coordinated"},
    }


def _mechanism(workspace: Path, python: str) -> dict:
    program = (
        f"from {PACKAGE} import observer, target\n"
        f"data = {HIDDEN_DATA!r}\n"
        "prepared = observer.prepare_input(data)\n"
        "assert prepared is not data\n"
        "assert target.answer(prepared, (0, 1, 2, 9)) == [10, 25, 0, 0]\n"
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


def _benchmark(workspace: Path, python: str) -> dict:
    samples = []
    for _ in range(15):
        result = _run([python, "benchmark.py"], workspace, 300)
        if result["returncode"] != 0:
            return {"success": False, "samples": samples, "failed_run": result}
        try:
            samples.append(_parse_benchmark(result["stdout"]))
        except (ValueError, SyntaxError, KeyError, TypeError):
            return {"success": False, "samples": samples, "failed_run": result}
    steady = sorted(samples)[:max(3, len(samples) // 2)]
    steady_seconds = statistics.median(steady)
    mad = statistics.median(abs(value - steady_seconds) for value in steady)
    return {
        "success": True,
        "rounds": len(samples),
        "all_seconds": samples,
        "median_seconds": statistics.median(samples),
        "steady_seconds": steady_seconds,
        "steady_relative_mad": mad / steady_seconds if steady_seconds else 0.0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--profile", choices=("neutral", "e1v2", "e1v3"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--python",
        default="/Users/haiyan-infiniai/.cache/codex-runtimes/"
        "codex-primary-runtime/dependencies/python/bin/python",
    )
    args = parser.parse_args(argv)
    workspace, seed = args.workspace.resolve(), args.seed.resolve()
    custody = _custody(workspace, seed)
    correctness = _correctness(workspace, args.python)
    topology = _topology(workspace, seed, args.profile)
    mechanism = _mechanism(workspace, args.python) if args.profile != "neutral" else None
    benchmark = _benchmark(workspace, args.python)
    checks = {
        "custody": custody["passed"],
        "correctness": correctness["success"],
        "topology": topology["passed"],
        "semantic_mechanism": args.profile == "neutral" or mechanism["success"],
        "benchmark": benchmark["success"],
    }
    report = {
        "schema": "modus-performance-p2l-cell-verification-v1",
        "profile": args.profile,
        "checks": checks,
        "passed": all(checks.values()),
        "implementation_digest": _implementation_digest(workspace),
        "custody": custody,
        "correctness": correctness,
        "topology": topology,
        "semantic_mechanism": mechanism,
        "benchmark": benchmark,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "passed": report["passed"],
        "profile": args.profile,
        "seconds": benchmark.get("steady_seconds"),
        "implementation_digest": report["implementation_digest"],
    }, sort_keys=True))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

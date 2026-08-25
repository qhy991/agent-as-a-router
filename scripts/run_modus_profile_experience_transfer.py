#!/usr/bin/env python3
"""Run the frozen staged Profile experience transfer Workers without retry."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.codex_spark_wave import run_wave  # noqa: E402


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def resolve_strategy_artifact(
    strategy: dict, *, strategy_root: Path, unconstrained_profile: Path,
) -> Path:
    repository = strategy["artifact_repository"]
    if repository == "generated-empty":
        path = unconstrained_profile.resolve()
    elif repository == "dsh-personal-plugins":
        path = (strategy_root.resolve() / strategy["artifact_path"]).resolve()
    else:
        raise RuntimeError("strategy artifact repository is unsupported")
    if not path.is_file():
        raise RuntimeError("strategy artifact is missing")
    if hashlib.sha256(path.read_bytes()).hexdigest() != strategy["artifact_sha256"]:
        raise RuntimeError("strategy artifact digest differs")
    return path


def derive_cells(protocol: dict, router_score: dict) -> list[dict]:
    if (
        router_score.get("status") != "pass"
        or router_score.get("worker_acquisition_authorized") is not True
    ):
        raise RuntimeError("Router score does not authorize Worker acquisition")
    routes = router_score["parsed"]["routes"]
    by_task = {row["task_id"]: row for row in routes}
    baseline = protocol["execution"]["fixed_baseline_strategy"]
    cells = []
    order = 1
    for task_id in protocol["router"]["tasks"]:
        route = by_task.get(task_id)
        if route is None:
            raise RuntimeError("Router score omits a task")
        selected = baseline if route["decision"] == "abstain" else route["strategy"]
        if selected is None:
            raise RuntimeError("Router requested qualification")
        cells.append({
            "id": f"{task_id}--reference",
            "task_id": task_id,
            "strategy": baseline,
            "role": "fixed-reference",
            "order": order,
        })
        order += 1
        if selected != baseline:
            cells.append({
                "id": f"{task_id}--selected",
                "task_id": task_id,
                "strategy": selected,
                "role": "router-selected",
                "order": order,
            })
            order += 1
    minimum, maximum = protocol["execution"]["authorized_worker_range"]
    if not minimum <= len(cells) <= maximum:
        raise RuntimeError("derived Worker count is outside the frozen range")
    return cells


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--router-score", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--strategy-root", type=Path, required=True)
    parser.add_argument(
        "--unconstrained-profile",
        type=Path,
        default=Path("/private/tmp/modus-profile-unconstrained.md"),
    )
    parser.add_argument(
        "--environment-bin",
        type=Path,
        required=True,
    )
    args = parser.parse_args(argv)
    protocol_path = args.protocol.resolve()
    repository = protocol_path.parents[1]
    protocol = json.loads(protocol_path.read_text())
    router_score = json.loads(args.router_score.read_text())
    root = args.run_root.resolve()
    if root.exists():
        raise RuntimeError("run root already exists")
    root.mkdir(parents=True)
    cells = derive_cells(protocol, router_score)
    results = []
    for cell in cells:
        cell_root = root / "cells" / cell["id"]
        workspace = cell_root / "workspace"
        workspace.parent.mkdir(parents=True)
        task = protocol["tasks"][cell["task_id"]]
        strategy = protocol["strategies"][cell["strategy"]]
        strategy_artifact = resolve_strategy_artifact(
            strategy,
            strategy_root=args.strategy_root,
            unconstrained_profile=args.unconstrained_profile,
        )
        seed = (repository / task["seed_root"]).resolve()
        shutil.copytree(seed, workspace)
        manifest = {
            "schema": "acrouter-codex-spark-wave-v1",
            "model": protocol["model"]["local_slug"],
            "reasoning_effort": protocol["model"]["reasoning_effort"],
            "timeout_seconds": 1800,
            "automatic_redispatch": False,
            "cells": [{
                "cell": cell["id"],
                "workspace": str(workspace),
                "profile": str(strategy_artifact),
                "profile_sha256": strategy["artifact_sha256"],
                "task": str((repository / task["prompt"]).resolve()),
                "task_sha256": task["prompt_sha256"],
                "environment_bin": str(args.environment_bin.resolve()),
            }],
        }
        manifest_path = cell_root / "manifest.json"
        _write(manifest_path, manifest)
        wave = run_wave(manifest_path, cell_root / "output", codex=args.codex)
        verification = cell_root / "verification.json"
        done = subprocess.run([
            sys.executable,
            str(repository / "scripts/verify_modus_profile_experience_cell.py"),
            "--workspace", str(workspace),
            "--seed", str(seed),
            "--task", cell["task_id"],
            "--strategy", cell["strategy"],
            "--output", str(verification),
            "--python", sys.executable,
        ], cwd=repository, check=False)
        valid = wave["status"] == "pass" and done.returncode == 0
        results.append({**cell, "status": "pass" if valid else "fail"})
    summary = {
        "schema": "modus-profile-experience-transfer-execution-v1",
        "automatic_redispatches": 0,
        "derived_worker_cells": len(cells),
        "cells": results,
        "status": "pass" if all(row["status"] == "pass" for row in results) else "fail",
    }
    _write(root / "execution-summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Execute the frozen invariant-specialization calibration matrix."""

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


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def strategy_artifact(strategy: dict, strategy_root: Path) -> Path:
    path = (strategy_root.resolve() / strategy["artifact_path"]).resolve()
    if not path.is_file():
        raise RuntimeError("strategy artifact is missing")
    if hashlib.sha256(path.read_bytes()).hexdigest() != strategy["artifact_sha256"]:
        raise RuntimeError("strategy artifact digest differs")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--codex", required=True)
    parser.add_argument("--strategy-root", type=Path, required=True)
    parser.add_argument("--environment-bin", type=Path, required=True)
    args = parser.parse_args(argv)
    protocol_path = args.protocol.resolve()
    repository = protocol_path.parents[1]
    protocol = json.loads(protocol_path.read_text())
    root = args.run_root.resolve()
    if root.exists():
        raise RuntimeError("run root already exists")
    root.mkdir(parents=True)
    rows = []
    for cell in protocol["cells"]:
        cell_root = root / "cells" / cell["id"]
        workspace = cell_root / "workspace"
        workspace.parent.mkdir(parents=True)
        task = protocol["tasks"][cell["task_id"]]
        strategy = protocol["strategies"][cell["strategy"]]
        seed = (repository / task["seed_root"]).resolve()
        shutil.copytree(seed, workspace)
        artifact = strategy_artifact(strategy, args.strategy_root)
        manifest = {
            "schema": "acrouter-codex-spark-wave-v1",
            "model": protocol["model"]["local_slug"],
            "reasoning_effort": protocol["model"]["reasoning_effort"],
            "timeout_seconds": 1800,
            "automatic_redispatch": False,
            "cells": [{
                "cell": cell["id"],
                "workspace": str(workspace),
                "profile": str(artifact),
                "profile_sha256": strategy["artifact_sha256"],
                "task": str((repository / task["prompt"]).resolve()),
                "task_sha256": task["prompt_sha256"],
                "environment_bin": str(args.environment_bin.resolve()),
            }],
        }
        manifest_path = cell_root / "manifest.json"
        write_json(manifest_path, manifest)
        wave = run_wave(manifest_path, cell_root / "output", codex=args.codex)
        verification_path = cell_root / "verification.json"
        verified = subprocess.run([
            sys.executable,
            str(repository / "scripts/verify_modus_invariant_specialization_cell.py"),
            "--workspace", str(workspace),
            "--seed", str(seed),
            "--task", cell["task_id"],
            "--strategy", cell["strategy"],
            "--output", str(verification_path),
            "--python", sys.executable,
        ], cwd=repository, check=False)
        valid = wave["status"] == "pass" and verified.returncode == 0
        rows.append({**cell, "status": "pass" if valid else "fail"})
    summary = {
        "schema": "modus-invariant-specialization-execution-v1",
        "planned_cells": len(protocol["cells"]),
        "automatic_redispatches": 0,
        "cells": rows,
        "status": "pass" if all(row["status"] == "pass" for row in rows) else "fail",
    }
    write_json(root / "execution-summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

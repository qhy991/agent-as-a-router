#!/usr/bin/env python3
"""Execute the frozen P2l three-Profile triplet sequentially and without retry."""

from __future__ import annotations

import argparse
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


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _manifest(
    *, protocol: dict, repo: Path, row: dict, workspace: Path,
    environment_bin: Path,
) -> dict:
    profile = protocol["profiles"][row["profile"]]
    return {
        "schema": "acrouter-codex-spark-wave-v1",
        "model": protocol["model"]["local_slug"],
        "reasoning_effort": protocol["model"]["reasoning_effort"],
        "timeout_seconds": 1800,
        "automatic_redispatch": False,
        "cells": [{
            "cell": row["id"],
            "workspace": str(workspace),
            "profile": profile["profile_path"],
            "profile_sha256": profile["profile_sha256"],
            "task": str((repo / protocol["task"]["prompt"]).resolve()),
            "task_sha256": protocol["task"]["prompt_sha256"],
            "environment_bin": str(environment_bin),
        }],
    }


def _verify(
    *, repo: Path, workspace: Path, seed: Path, profile: str, output: Path,
) -> bool:
    completed = subprocess.run([
        sys.executable,
        str(repo / "scripts/verify_modus_performance_p2l_cell.py"),
        "--workspace", str(workspace),
        "--seed", str(seed),
        "--profile", profile,
        "--output", str(output),
        "--python", sys.executable,
    ], cwd=repo, check=False)
    return completed.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--codex", default="codex")
    parser.add_argument(
        "--environment-bin",
        type=Path,
        default=Path(
            "/Users/haiyan-infiniai/.cache/codex-runtimes/"
            "codex-primary-runtime/dependencies/python/bin"
        ),
    )
    args = parser.parse_args(argv)
    protocol_path = args.protocol.resolve()
    repo = protocol_path.parents[1]
    protocol = json.loads(protocol_path.read_text())
    run_root = args.run_root.resolve()
    if run_root.exists():
        raise RuntimeError("run root already exists")
    run_root.mkdir(parents=True)
    seed = (repo / protocol["task"]["seed_root"]).resolve()
    rows = []
    for cell in protocol["cells"]:
        cell_root = run_root / "cells" / cell["id"]
        workspace = cell_root / "workspace"
        workspace.parent.mkdir(parents=True)
        shutil.copytree(seed, workspace)
        manifest = _manifest(
            protocol=protocol,
            repo=repo,
            row=cell,
            workspace=workspace,
            environment_bin=args.environment_bin.resolve(),
        )
        manifest_path = cell_root / "manifest.json"
        _write_json(manifest_path, manifest)
        wave = run_wave(manifest_path, cell_root / "output", codex=args.codex)
        verification = cell_root / "verification.json"
        valid = wave["status"] == "pass" and _verify(
            repo=repo,
            workspace=workspace,
            seed=seed,
            profile=cell["profile"],
            output=verification,
        )
        rows.append({**cell, "status": "pass" if valid else "fail"})

    summary = {
        "schema": "modus-performance-p2l-execution-v1",
        "automatic_redispatches": 0,
        "cells": rows,
        "status": "pass" if all(row["status"] == "pass" for row in rows) else "fail",
    }
    _write_json(run_root / "execution-summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

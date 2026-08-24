#!/usr/bin/env python3
"""Execute the frozen linked P2a pipelines once, sequentially and fail-closed."""

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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _stage_manifest(
    *, protocol: dict, repo: Path, pipeline: dict, stage: str,
    workspace: Path, environment_bin: Path,
) -> dict:
    arm = protocol["arms"][pipeline["arm"]]
    profile = arm[f"stage-{stage}"]
    profile_record = protocol["profiles"][profile]
    prompt_key = "stage_l_prompt" if stage == "L" else "stage_s_prompt"
    prompt_hash_key = prompt_key + "_sha256"
    return {
        "schema": "acrouter-codex-spark-wave-v1",
        "model": protocol["model"]["local_slug"],
        "reasoning_effort": protocol["model"]["reasoning_effort"],
        "timeout_seconds": 1800,
        "automatic_redispatch": False,
        "cells": [{
            "cell": f"{pipeline['id']}-stage-{stage.lower()}",
            "workspace": str(workspace),
            "profile": profile_record["profile_path"],
            "profile_sha256": profile_record["profile_sha256"],
            "task": str((repo / protocol["task"][prompt_key]).resolve()),
            "task_sha256": protocol["task"][prompt_hash_key],
            "environment_bin": str(environment_bin),
        }],
    }


def _verify(
    *, repo: Path, workspace: Path, seed: Path, stage: str,
    arm: str, profile: str, output: Path, parent: Path | None,
) -> bool:
    command = [
        sys.executable,
        str(repo / "scripts/verify_modus_long_horizon_p2a_stage.py"),
        "--workspace", str(workspace), "--seed", str(seed),
        "--stage", stage, "--arm", arm, "--profile", profile,
        "--output", str(output), "--python", sys.executable,
    ]
    if parent is not None:
        command.extend(["--parent-record", str(parent)])
    completed = subprocess.run(command, cwd=repo, check=False)
    return completed.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--codex", default="codex")
    parser.add_argument(
        "--environment-bin", type=Path,
        default=Path("/Users/haiyan-infiniai/.cache/codex-runtimes/"
                     "codex-primary-runtime/dependencies/python/bin"),
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
    for pipeline in protocol["pipelines"]:
        pipeline_root = run_root / "pipelines" / pipeline["id"]
        workspace = pipeline_root / "workspace"
        workspace.parent.mkdir(parents=True)
        shutil.copytree(seed, workspace)
        arm = protocol["arms"][pipeline["arm"]]
        row = {**pipeline, "stage_l": "not-started", "stage_s": "not-started"}

        l_manifest = _stage_manifest(
            protocol=protocol, repo=repo, pipeline=pipeline, stage="L",
            workspace=workspace, environment_bin=args.environment_bin.resolve(),
        )
        l_manifest_path = pipeline_root / "stage-l-manifest.json"
        _write_json(l_manifest_path, l_manifest)
        l_result = run_wave(
            l_manifest_path, pipeline_root / "stage-l-output", codex=args.codex
        )
        l_verification = pipeline_root / "stage-l-verification.json"
        l_ok = l_result["status"] == "pass" and _verify(
            repo=repo, workspace=workspace, seed=seed, stage="L",
            arm=pipeline["arm"], profile=arm["stage-L"],
            output=l_verification, parent=None,
        )
        row["stage_l"] = "pass" if l_ok else "fail"
        if not l_ok:
            rows.append(row)
            continue

        l_value = json.loads(l_verification.read_text())
        parent = pipeline_root / "stage-s-parent.json"
        _write_json(parent, {
            "schema": "modus-long-horizon-p2a-parent-v1",
            "implementation_digest": l_value["implementation_digest"],
            "stage_l_verification_sha256": _sha256(l_verification),
        })
        s_manifest = _stage_manifest(
            protocol=protocol, repo=repo, pipeline=pipeline, stage="S",
            workspace=workspace, environment_bin=args.environment_bin.resolve(),
        )
        s_manifest_path = pipeline_root / "stage-s-manifest.json"
        _write_json(s_manifest_path, s_manifest)
        s_result = run_wave(
            s_manifest_path, pipeline_root / "stage-s-output", codex=args.codex
        )
        s_ok = s_result["status"] == "pass" and _verify(
            repo=repo, workspace=workspace, seed=seed, stage="S",
            arm=pipeline["arm"], profile=arm["stage-S"],
            output=pipeline_root / "stage-s-verification.json", parent=parent,
        )
        row["stage_s"] = "pass" if s_ok else "fail"
        rows.append(row)

    summary = {
        "schema": "modus-long-horizon-p2a-execution-v1",
        "automatic_redispatches": 0,
        "pipelines": rows,
        "status": "pass" if all(
            row["stage_l"] == row["stage_s"] == "pass" for row in rows
        ) else "fail",
    }
    _write_json(run_root / "execution-summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

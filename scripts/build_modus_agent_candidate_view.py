#!/usr/bin/env python3
"""Derive an Agent-facing candidate view with canonical abstain vocabulary."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.modus_mechanism_registry import (  # noqa: E402
    load_mechanism_registry,
    match_typed_mechanisms,
    resolve_typed_candidates,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--descriptors", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    registry = load_mechanism_registry(args.registry)
    descriptor_file = json.loads(args.descriptors.read_text())
    if (
        not isinstance(descriptor_file, dict)
        or set(descriptor_file) != {"schema", "stages"}
        or descriptor_file["schema"] != "modus-typed-stage-descriptors-v1"
        or not isinstance(descriptor_file["stages"], list)
        or not descriptor_file["stages"]
    ):
        raise ValueError("typed descriptor file is invalid")
    rows = []
    stages = set()
    for row in descriptor_file["stages"]:
        if not isinstance(row, dict) or set(row) != {
            "stage", "worker_model", "semantic_kind", "reuse_batches",
            "performance_objective",
        }:
            raise ValueError("typed stage descriptor fields differ")
        stage = row["stage"]
        if not isinstance(stage, str) or not stage or stage in stages:
            raise ValueError("typed stage is invalid or duplicated")
        stages.add(stage)
        descriptor = {key: value for key, value in row.items() if key != "stage"}
        matches = match_typed_mechanisms(registry, descriptor)
        resolution = resolve_typed_candidates(matches)
        if resolution["decision"] == "defer":
            resolution = {**resolution, "decision": "abstain"}
        rows.append({
            "stage": stage,
            "descriptor": descriptor,
            "resolution": resolution,
        })
    result = {
        "schema": "modus-derived-qualified-candidate-view-v1",
        "registry_sha256": hashlib.sha256(args.registry.read_bytes()).hexdigest(),
        "descriptor_sha256": hashlib.sha256(args.descriptors.read_bytes()).hexdigest(),
        "stages": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(args.output),
        "decisions": {row["stage"]: row["resolution"]["decision"] for row in rows},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

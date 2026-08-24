#!/usr/bin/env python3
"""Build one evidence-bound Modus route cache entry from a verified Router score."""

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

from acrouter_repro.modus_route_cache import build_entry, build_key  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text())
    expected = {
        "schema", "task_contract_sha256", "typed_descriptor",
        "router_prompt_sha256", "model", "allowed_actions", "profile_digests",
        "router_score_path",
    }
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError("route cache build config fields differ")
    if config["schema"] != "modus-route-cache-build-v1":
        raise ValueError("route cache build config schema differs")
    evidence_root = args.evidence_root.resolve()
    score_path = evidence_root / config["router_score_path"]
    score = json.loads(score_path.read_text())
    if score.get("status") != "pass" or not score.get("pipeline_protocol_authorized"):
        raise ValueError("Router score is not a valid authorized decision")
    actions = score.get("stable_actions_by_stage")
    usage = score.get("router_acquisition_tokens")
    if not isinstance(actions, dict) or not isinstance(usage, int) or usage <= 0:
        raise ValueError("Router score decision or usage is invalid")
    key = build_key(
        task_contract_sha256=config["task_contract_sha256"],
        typed_descriptor=config["typed_descriptor"],
        router_prompt_sha256=config["router_prompt_sha256"],
        model_slug=config["model"]["slug"],
        reasoning_effort=config["model"]["reasoning_effort"],
        allowed_actions=config["allowed_actions"],
        profile_digests=config["profile_digests"],
    )
    entry = build_entry(
        key=key,
        decision={"actions_by_stage": actions},
        router_score_path=config["router_score_path"],
        router_score_sha256=hashlib.sha256(score_path.read_bytes()).hexdigest(),
        router_usage_tokens=usage,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(args.output), "key_sha256": entry["key_sha256"],
        "decision_sha256": entry["decision_sha256"], "router_usage_tokens": usage,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

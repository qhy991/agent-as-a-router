#!/usr/bin/env python3
"""Build a derived outcome qualification envelope for one cached Modus route."""

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

from acrouter_repro.modus_route_qualification import build_envelope  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text())
    expected = {
        "schema", "route_entry_path", "outcome_evidence_path", "policy", "observed",
    }
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError("qualification build config fields differ")
    if config["schema"] != "modus-route-qualification-build-v1":
        raise ValueError("qualification build config schema differs")
    root = args.evidence_root.resolve()
    entry_path = root / config["route_entry_path"]
    outcome_path = root / config["outcome_evidence_path"]
    entry = json.loads(entry_path.read_text())
    envelope = build_envelope(
        route_entry_path=config["route_entry_path"],
        route_entry=entry,
        route_entry_sha256=hashlib.sha256(entry_path.read_bytes()).hexdigest(),
        outcome_evidence_path=config["outcome_evidence_path"],
        outcome_evidence_sha256=hashlib.sha256(outcome_path.read_bytes()).hexdigest(),
        policy=config["policy"],
        observed=config["observed"],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(args.output), "status": envelope["status"],
        "route_entry_sha256": envelope["route_entry_sha256"],
        "outcome_evidence_sha256": envelope["outcome_evidence_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

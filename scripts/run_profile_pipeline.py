#!/usr/bin/env python3
"""Replay a fixed behavioral-Profile matrix with constrained ACRouter metrics."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--cells", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from acrouter_repro.profile_pipeline import analyze_profile_file

    result = analyze_profile_file(args.config, args.cells, args.output_dir)
    best_fixed = result["best_fixed_profile"] or {}
    print(
        "ProfileReplay "
        f"tasks={len(result['tasks'])} "
        f"best_fixed={best_fixed.get('profile')} "
        f"oracle_actions={','.join(result['oracle']['distinct_actions']) or 'none'} "
        f"saving={result['oracle']['saving_fraction_vs_best_fixed']} "
        f"routing_space={str(result['routing_space']['observed']).lower()} "
        f"status={result['claim_status']}"
    )
    print(f"result={args.output_dir / 'profile_replay.json'}")


if __name__ == "__main__":
    main()

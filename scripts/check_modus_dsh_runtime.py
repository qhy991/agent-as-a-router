#!/usr/bin/env python3
"""Validate a pinned Modus plus DSH runtime before any model request."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.dsh_preflight import run_dsh_preflight, write_preflight_report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dsh-root", type=Path, required=True)
    result.add_argument("--plugin-root", type=Path, required=True)
    result.add_argument("--expected-plugin-commit", required=True)
    result.add_argument("--report", type=Path, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    options = parser().parse_args(argv)
    report = run_dsh_preflight(
        dsh_root=options.dsh_root,
        plugin_root=options.plugin_root,
        expected_plugin_commit=options.expected_plugin_commit,
    )
    write_preflight_report(report, options.report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

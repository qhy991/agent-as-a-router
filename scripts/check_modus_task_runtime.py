#!/usr/bin/env python3
"""Verify a local SWE task runtime before starting a Modus model cell."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.dsh_preflight import write_preflight_report
from acrouter_repro.task_runtime_preflight import run_task_runtime_preflight


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--workspace", type=Path, required=True)
    result.add_argument("--isolated-home", type=Path, required=True)
    result.add_argument("--mamba-root", type=Path, required=True)
    result.add_argument("--environment", required=True)
    result.add_argument("--report", type=Path, required=True)
    result.add_argument(
        "python_arguments",
        nargs=argparse.REMAINDER,
        help="arguments after -- are passed to Python inside the declared environment",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    options = parser().parse_args(argv)
    arguments = options.python_arguments
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    report = run_task_runtime_preflight(
        workspace=options.workspace,
        isolated_home=options.isolated_home,
        mamba_root=options.mamba_root,
        environment_name=options.environment,
        python_arguments=arguments,
    )
    write_preflight_report(report, options.report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

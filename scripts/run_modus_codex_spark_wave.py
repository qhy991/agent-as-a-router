#!/usr/bin/env python3
"""Run one frozen local Codex wave exactly once."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.codex_spark_wave import run_wave


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--codex", default="codex")
    options = parser.parse_args(argv)
    result = run_wave(options.manifest, options.output, codex=options.codex)
    print(json.dumps({
        "status": result["status"],
        "valid_execution_cells": result["valid_execution_cells"],
        "cells": len(result["cells"]),
    }, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())

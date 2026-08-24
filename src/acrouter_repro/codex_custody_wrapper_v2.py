#!/usr/bin/env python3
"""Launch Codex from the allowed workspace under the P2o read sandbox."""

from __future__ import annotations

import os
from pathlib import Path
import sys

from acrouter_repro.codex_custody_wrapper import build_profile


def main() -> None:
    args = sys.argv[1:]
    try:
        workspace = Path(args[args.index("-C") + 1]).resolve()
    except (ValueError, IndexError) as error:
        raise SystemExit("custody wrapper requires Codex -C workspace") from error
    deny_roots = [
        Path(value) for value in os.environ.get("MODUS_CUSTODY_DENY_ROOTS", "").split(os.pathsep)
        if value
    ]
    if not deny_roots:
        raise SystemExit("MODUS_CUSTODY_DENY_ROOTS is empty")
    profile = build_profile(workspace, deny_roots)
    real_codex = os.environ.get("MODUS_REAL_CODEX", "/Users/haiyan-infiniai/.local/bin/codex")
    os.chdir(workspace)
    os.execv("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", profile, real_codex, *args])


if __name__ == "__main__":
    main()

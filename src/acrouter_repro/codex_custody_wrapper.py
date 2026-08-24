#!/usr/bin/env python3
"""Launch Codex under a macOS read-custody sandbox for one experiment cell."""

from __future__ import annotations

import os
from pathlib import Path
import sys


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_profile(workspace: Path, deny_roots: list[Path]) -> str:
    workspace = workspace.resolve()
    cell_root = workspace.parent
    run_root = cell_root.parents[1]
    lines = [
        "(version 1)",
        "(allow default)",
        f"(deny file-read* (subpath {_quote(str(run_root))}))",
        f"(allow file-read* (subpath {_quote(str(cell_root))}))",
    ]
    for root in sorted({path.resolve() for path in deny_roots}):
        if root != run_root and root not in cell_root.parents:
            lines.append(f"(deny file-read* (subpath {_quote(str(root))}))")
    return " ".join(lines)


def main() -> None:
    args = sys.argv[1:]
    try:
        workspace = Path(args[args.index("-C") + 1])
    except (ValueError, IndexError) as error:
        raise SystemExit("custody wrapper requires Codex -C workspace") from error
    deny_roots = [
        Path(value) for value in os.environ.get("MODUS_CUSTODY_DENY_ROOTS", "").split(os.pathsep)
        if value
    ]
    if not deny_roots:
        raise SystemExit("MODUS_CUSTODY_DENY_ROOTS is empty")
    real_codex = os.environ.get("MODUS_REAL_CODEX", "/Users/haiyan-infiniai/.local/bin/codex")
    profile = build_profile(workspace, deny_roots)
    os.execv("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", profile, real_codex, *args])


if __name__ == "__main__":
    main()

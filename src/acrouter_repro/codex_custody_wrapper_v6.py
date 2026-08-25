#!/usr/bin/env python3
"""Confine Codex reads and temporary files to the current experiment cell."""

from __future__ import annotations

import os
from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.codex_custody_wrapper import _quote


def build_profile(workspace: Path, deny_roots: list[Path]) -> str:
    workspace = workspace.resolve()
    cell_root = workspace.parent
    private_tmp = Path("/private/tmp")
    lines = [
        "(version 1)",
        "(allow default)",
        f"(deny file-read* (subpath {_quote(str(private_tmp))}))",
        f"(allow file-read-metadata (subpath {_quote(str(private_tmp))}))",
        f"(allow file-read* (subpath {_quote(str(cell_root))}))",
    ]
    for root in sorted({path.resolve() for path in deny_roots}):
        if private_tmp not in root.parents and root != private_tmp:
            lines.append(f"(deny file-read* (subpath {_quote(str(root))}))")
    return " ".join(lines)


def main() -> None:
    args = sys.argv[1:]
    workspace = Path(args[args.index("-C") + 1]).resolve()
    deny_roots = [
        Path(value) for value in os.environ.get("MODUS_CUSTODY_DENY_ROOTS", "").split(os.pathsep)
        if value
    ]
    if not deny_roots:
        raise SystemExit("MODUS_CUSTODY_DENY_ROOTS is empty")
    args[args.index("--sandbox") + 1] = "danger-full-access"
    cell_tmp = workspace.parent / "tmp"
    cell_tmp.mkdir(exist_ok=True)
    os.environ.update({"TMPDIR": str(cell_tmp), "TMP": str(cell_tmp), "TEMP": str(cell_tmp)})
    profile = build_profile(workspace, deny_roots)
    real_codex = os.environ.get("MODUS_REAL_CODEX", "/Users/haiyan-infiniai/.local/bin/codex")
    os.chdir(workspace)
    os.execv("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", profile, real_codex, *args])


if __name__ == "__main__":
    main()

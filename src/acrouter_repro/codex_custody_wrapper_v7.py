#!/usr/bin/env python3
"""Confine Worker reads to one cell, its artifacts, and explicit runtimes."""

from __future__ import annotations

import os
from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from acrouter_repro.codex_custody_wrapper import _quote


def _within(path: Path, root: Path) -> bool:
    path = path.resolve()
    root = root.resolve()
    return path == root or root in path.parents


def build_profile(
    workspace: Path,
    deny_roots: list[Path],
    *,
    home_root: Path,
    runtime_roots: list[Path],
    control_processes: list[Path],
    artifact_roots: list[Path] | None = None,
) -> str:
    workspace = workspace.resolve()
    cell_root = workspace.parent
    private_tmp = Path("/private/tmp")
    home_root = home_root.resolve()
    runtimes = sorted({path.resolve() for path in runtime_roots})
    controls = sorted({path.expanduser().absolute() for path in control_processes})
    artifacts = sorted({path.resolve() for path in artifact_roots or []})
    if not runtimes:
        raise ValueError("custody runtime roots are empty")
    if any(root == home_root for root in runtimes):
        raise ValueError("custody runtime root may not expose the entire home")
    if not controls:
        raise ValueError("custody control processes are empty")
    lines = [
        "(version 1)",
        "(allow default)",
        f"(deny file-read* (subpath {_quote(str(private_tmp))}))",
        f"(allow file-read-metadata (subpath {_quote(str(private_tmp))}))",
        f"(deny file-read* (subpath {_quote(str(home_root))}))",
        f"(allow file-read-metadata (subpath {_quote(str(home_root))}))",
        f"(allow file-read* (subpath {_quote(str(cell_root))}))",
    ]
    lines.extend(
        f"(allow file-read* (subpath {_quote(str(root))}))" for root in artifacts
    )
    lines.extend(
        f"(allow file-read* (subpath {_quote(str(root))}))" for root in runtimes
    )
    lines.extend(
        "(allow file-read* (require-all "
        f"(subpath {_quote(str(home_root))}) "
        f"(process-path {_quote(str(process))})))"
        for process in controls
    )
    for root in sorted({path.resolve() for path in deny_roots}):
        if private_tmp not in root.parents and root != private_tmp:
            lines.append(f"(deny file-read* (subpath {_quote(str(root))}))")
    return " ".join(lines)


def main() -> None:
    args = sys.argv[1:]
    workspace = Path(args[args.index("-C") + 1]).resolve()
    deny_roots = [
        Path(value)
        for value in os.environ.get("MODUS_CUSTODY_DENY_ROOTS", "").split(os.pathsep)
        if value
    ]
    home_value = os.environ.get("MODUS_CUSTODY_HOME_ROOT")
    runtime_roots = [
        Path(value)
        for value in os.environ.get("MODUS_CUSTODY_RUNTIME_ROOTS", "").split(os.pathsep)
        if value
    ]
    control_processes = [
        Path(value)
        for value in os.environ.get("MODUS_CUSTODY_CONTROL_PROCESSES", "").split(
            os.pathsep
        )
        if value
    ]
    if not deny_roots:
        raise SystemExit("MODUS_CUSTODY_DENY_ROOTS is empty")
    if not home_value:
        raise SystemExit("MODUS_CUSTODY_HOME_ROOT is empty")
    if not runtime_roots:
        raise SystemExit("MODUS_CUSTODY_RUNTIME_ROOTS is empty")
    if not control_processes:
        raise SystemExit("MODUS_CUSTODY_CONTROL_PROCESSES is empty")
    home_root = Path(home_value).resolve()
    real_codex = Path(
        os.environ.get("MODUS_REAL_CODEX", "/Users/haiyan-infiniai/.local/bin/codex")
    ).resolve()
    if not any(_within(real_codex, root) for root in runtime_roots):
        raise SystemExit("real Codex is outside custody runtime roots")
    if not all(
        any(_within(process, root) for root in runtime_roots)
        for process in control_processes
    ):
        raise SystemExit("custody control process is outside runtime roots")
    args[args.index("--sandbox") + 1] = "danger-full-access"
    output_root = (
        Path(args[args.index("-o") + 1]).resolve().parent if "-o" in args else None
    )
    cell_tmp = workspace.parent / "tmp"
    cell_tmp.mkdir(exist_ok=True)
    os.environ.update(
        {"TMPDIR": str(cell_tmp), "TMP": str(cell_tmp), "TEMP": str(cell_tmp)}
    )
    profile = build_profile(
        workspace,
        deny_roots,
        home_root=home_root,
        runtime_roots=runtime_roots,
        control_processes=control_processes,
        artifact_roots=[output_root] if output_root else [],
    )
    os.chdir(workspace)
    os.execv(
        "/usr/bin/sandbox-exec",
        ["sandbox-exec", "-p", profile, str(real_codex), *args],
    )


if __name__ == "__main__":
    main()

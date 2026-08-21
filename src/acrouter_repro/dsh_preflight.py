"""Fail-closed provenance preflight for Modus fixed-Worker experiments."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any


REPORT_SCHEMA = "acrouter-modus-dsh-preflight-v1"
COMPATIBILITY_SCHEMA = "dsh-modus-compatibility-v1"
REQUIRED_CONTRACT = "fixed-worker-auxiliary-tool-confinement"
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
CommandRunner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


class DshPreflightError(RuntimeError):
    """The runtime cannot support an attributable Modus experiment."""


def _default_runner(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise DshPreflightError(f"git {' '.join(arguments)} failed for {root.name}")
    return completed.stdout.strip()


def _inspect_repository(root: Path, expected_commit: str, label: str) -> dict[str, Any]:
    if not COMMIT_PATTERN.fullmatch(expected_commit):
        raise DshPreflightError(f"{label} expected commit must be a full lowercase SHA-1")
    resolved = root.expanduser().resolve()
    if not resolved.is_dir():
        raise DshPreflightError(f"{label} root is not a directory")
    observed_commit = _git(resolved, "rev-parse", "HEAD")
    if observed_commit != expected_commit:
        raise DshPreflightError(
            f"{label} commit mismatch: expected {expected_commit}, observed {observed_commit}"
        )
    dirty = _git(resolved, "status", "--porcelain")
    if dirty:
        raise DshPreflightError(f"{label} worktree is dirty")
    return {"commit": observed_commit, "clean": True}


def _load_compatibility(plugin_root: Path) -> dict[str, Any]:
    path = plugin_root / "presets" / "modus" / "compatibility.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DshPreflightError("plugin compatibility manifest is missing or invalid") from error
    if value.get("schema") != COMPATIBILITY_SCHEMA:
        raise DshPreflightError("plugin compatibility schema is unsupported")
    contracts = value.get("contracts")
    if not isinstance(contracts, list) or REQUIRED_CONTRACT not in contracts:
        raise DshPreflightError(
            f"plugin compatibility manifest lacks required contract {REQUIRED_CONTRACT}"
        )
    expected_dsh = value.get("dsh", {}).get("tested_commit")
    if not isinstance(expected_dsh, str) or not COMMIT_PATTERN.fullmatch(expected_dsh):
        raise DshPreflightError("plugin compatibility manifest has no full DSH commit")
    return {"path": path, "expected_dsh_commit": expected_dsh, "contracts": contracts}


def _run_gate(
    *,
    name: str,
    command: Sequence[str],
    cwd: Path,
    runner: CommandRunner,
) -> dict[str, Any]:
    completed = runner(command, cwd)
    result = {
        "name": name,
        "returncode": completed.returncode,
        "stdout_sha256": _sha256_text(completed.stdout),
        "stderr_sha256": _sha256_text(completed.stderr),
    }
    if completed.returncode != 0:
        raise DshPreflightError(f"{name} failed with exit code {completed.returncode}")
    return result


def run_dsh_preflight(
    *,
    dsh_root: Path,
    plugin_root: Path,
    expected_plugin_commit: str,
    runner: CommandRunner = _default_runner,
) -> dict[str, Any]:
    """Verify source, dependency-lock, and real-runtime compatibility before dispatch."""
    dsh_root = dsh_root.expanduser().resolve()
    plugin_root = plugin_root.expanduser().resolve()
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "status": "fail",
        "model_requests": 0,
        "required_contract": REQUIRED_CONTRACT,
        "expected_plugin_commit": expected_plugin_commit,
        "gates": [],
        "error": None,
    }
    try:
        report["plugin"] = _inspect_repository(
            plugin_root, expected_plugin_commit, "plugin"
        )
        compatibility = _load_compatibility(plugin_root)
        report["compatibility_manifest_sha256"] = _sha256_file(compatibility["path"])
        report["dsh"] = _inspect_repository(
            dsh_root, compatibility["expected_dsh_commit"], "DSH"
        )

        lockfile = dsh_root / "pnpm-lock.yaml"
        if not lockfile.is_file():
            raise DshPreflightError("DSH pnpm-lock.yaml is missing")
        pnpm = shutil.which("pnpm")
        if pnpm is None:
            raise DshPreflightError("pnpm is unavailable")
        report["pnpm_lock_sha256"] = _sha256_file(lockfile)
        report["gates"].append(_run_gate(
            name="frozen-offline-lockfile",
            command=[pnpm, "install", "--lockfile-only", "--frozen-lockfile", "--offline"],
            cwd=dsh_root,
            runner=runner,
        ))
        report["gates"].append(_run_gate(
            name="real-dsh-compatibility",
            command=[
                sys.executable,
                str(plugin_root / "scripts" / "check_dsh_compat.py"),
                "--dsh-root",
                str(dsh_root),
            ],
            cwd=plugin_root,
            runner=runner,
        ))

        # Both gates may execute package tooling. Re-check custody afterward.
        _inspect_repository(plugin_root, expected_plugin_commit, "plugin")
        _inspect_repository(dsh_root, compatibility["expected_dsh_commit"], "DSH")
        report["status"] = "pass"
    except DshPreflightError as error:
        report["error"] = str(error)
    return report


def write_preflight_report(report: dict[str, Any], destination: Path) -> None:
    """Atomically preserve either a pass or fail result."""
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)

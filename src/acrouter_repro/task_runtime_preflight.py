"""Model-free task-runtime qualification for local Modus SWE cells."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any


REPORT_SCHEMA = "acrouter-modus-task-runtime-preflight-v1"
SAFE_ENVIRONMENT_NAMES = (
    "PATH", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL", "LC_CTYPE", "TZ",
)
CommandRunner = Callable[
    [Sequence[str], Path, dict[str, str]],
    subprocess.CompletedProcess[str],
]


class TaskRuntimePreflightError(RuntimeError):
    """The declared task runtime is unavailable or not isolated."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def worker_environment(
    *,
    isolated_home: Path,
    mamba_root: Path,
    source: dict[str, str] | None = None,
) -> dict[str, str]:
    """Return the bounded environment shared by preflight and the Worker host."""
    ambient = os.environ if source is None else source
    result = {name: ambient[name] for name in SAFE_ENVIRONMENT_NAMES if name in ambient}
    result.update({
        "HOME": str(isolated_home.expanduser().resolve()),
        "MAMBA_ROOT_PREFIX": str(mamba_root.expanduser().resolve()),
        "PIP_NO_INDEX": "1",
        "PIP_REQUIRE_VIRTUALENV": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    return result


def _default_runner(
    command: Sequence[str],
    cwd: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def run_task_runtime_preflight(
    *,
    workspace: Path,
    isolated_home: Path,
    mamba_root: Path,
    environment_name: str,
    python_arguments: Sequence[str],
    runner: CommandRunner = _default_runner,
) -> dict[str, Any]:
    """Run the declared Python acceptance command without a model request."""
    workspace = workspace.expanduser().resolve()
    isolated_home = isolated_home.expanduser().resolve()
    mamba_root = mamba_root.expanduser().resolve()
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "status": "fail",
        "model_requests": 0,
        "environment_name": environment_name,
        "python_arguments": list(python_arguments),
        "environment_contract": {
            "isolated_home": True,
            "existing_mamba_root_bound": True,
            "pip_no_index": True,
            "pip_requires_virtualenv": True,
            "python_bytecode_disabled": True,
        },
        "error": None,
    }
    try:
        if not workspace.is_dir():
            raise TaskRuntimePreflightError("workspace is not a directory")
        if not environment_name or any(character.isspace() for character in environment_name):
            raise TaskRuntimePreflightError("environment name must be one non-empty token")
        if not python_arguments:
            raise TaskRuntimePreflightError("python arguments must not be empty")
        if (workspace == isolated_home
                or workspace in isolated_home.parents
                or isolated_home in workspace.parents):
            raise TaskRuntimePreflightError("isolated HOME and workspace must be disjoint")
        if (isolated_home == mamba_root
                or isolated_home in mamba_root.parents
                or mamba_root in isolated_home.parents):
            raise TaskRuntimePreflightError("isolated HOME and mamba root must be disjoint")
        python = mamba_root / "envs" / environment_name / "bin" / "python"
        if not python.is_file():
            raise TaskRuntimePreflightError("declared micromamba environment is missing")
        micromamba = shutil.which("micromamba")
        if micromamba is None:
            raise TaskRuntimePreflightError("micromamba is unavailable")
        isolated_home.mkdir(parents=True, exist_ok=True)
        environment = worker_environment(
            isolated_home=isolated_home,
            mamba_root=mamba_root,
        )
        command = [
            micromamba,
            "run",
            "-n",
            environment_name,
            "python",
            *python_arguments,
        ]
        completed = runner(command, workspace, environment)
        report["command"] = {
            "returncode": completed.returncode,
            "stdout_sha256": _sha256_text(completed.stdout),
            "stderr_sha256": _sha256_text(completed.stderr),
        }
        if completed.returncode != 0:
            raise TaskRuntimePreflightError(
                f"declared task command failed with exit code {completed.returncode}"
            )
        report["status"] = "pass"
    except TaskRuntimePreflightError as error:
        report["error"] = str(error)
    return report

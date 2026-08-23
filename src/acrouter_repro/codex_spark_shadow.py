"""No-retry local Codex execution for bounded Router shadow cells."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from .codex_spark_wave import _event_summary


MANIFEST_SCHEMAS = {
    "acrouter-codex-shadow-v1",
    "acrouter-codex-spark-shadow-v1",
}
RESULT_SCHEMA = "acrouter-codex-shadow-result-v1"
SUPPORTED_MODELS = {"gpt-5.3-codex-spark", "gpt-5.6-sol"}
ALLOWED_INITIAL_FILES = {"inbox/task.md"}
ALLOWED_FINAL_FILES = {"inbox/task.md", "outbox/route-response.json"}


class SparkShadowError(RuntimeError):
    """A shadow manifest or workspace violates the execution boundary."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _snapshot(path: str, digest: str, where: str) -> tuple[Path, str]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise SparkShadowError(f"{where} is missing")
    raw = resolved.read_bytes()
    if _sha256(raw) != digest:
        raise SparkShadowError(f"{where} digest differs")
    try:
        return resolved, raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SparkShadowError(f"{where} is not UTF-8") from error


def _workspace_files(workspace: Path) -> set[str]:
    return {
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file()
    }


def validate_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") not in MANIFEST_SCHEMAS:
        raise SparkShadowError("unsupported shadow manifest")
    if value.get("model") not in SUPPORTED_MODELS:
        raise SparkShadowError("unsupported local Codex shadow model")
    if value.get("automatic_redispatch") is not False:
        raise SparkShadowError("automatic_redispatch must be false")
    effort = value.get("reasoning_effort")
    if effort not in {"low", "medium", "high", "xhigh"}:
        raise SparkShadowError("unsupported reasoning effort")
    timeout = value.get("timeout_seconds")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise SparkShadowError("timeout_seconds must be positive")
    _, system_prompt = _snapshot(
        value.get("system_prompt", ""),
        value.get("system_prompt_sha256", ""),
        "system_prompt",
    )
    raw_cells = value.get("cells")
    if not isinstance(raw_cells, list) or not raw_cells:
        raise SparkShadowError("cells must be non-empty")
    ids: set[str] = set()
    workspaces: set[Path] = set()
    cells: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_cells):
        if not isinstance(raw, dict) or set(raw) != {"cell", "workspace", "task_sha256"}:
            raise SparkShadowError(f"cells[{index}] fields differ")
        cell = raw["cell"]
        workspace = Path(raw["workspace"]).expanduser().resolve()
        if not isinstance(cell, str) or not cell or "/" in cell or cell in ids:
            raise SparkShadowError(f"cells[{index}].cell is invalid")
        if not workspace.is_dir() or workspace in workspaces:
            raise SparkShadowError(f"cells[{index}].workspace is missing or duplicated")
        if _workspace_files(workspace) != ALLOWED_INITIAL_FILES:
            raise SparkShadowError(f"cells[{index}].workspace initial files differ")
        task = workspace / "inbox" / "task.md"
        task_raw = task.read_bytes()
        if _sha256(task_raw) != raw["task_sha256"]:
            raise SparkShadowError(f"cells[{index}].task digest differs")
        ids.add(cell)
        workspaces.add(workspace)
        cells.append({"cell": cell, "workspace": workspace})
    return {
        "model": value["model"],
        "reasoning_effort": effort,
        "timeout_seconds": timeout,
        "system_prompt": system_prompt,
        "system_prompt_sha256": value["system_prompt_sha256"],
        "manifest_sha256": _sha256(path.read_bytes()),
        "cells": cells,
    }


def _run_cell(cell: dict[str, Any], plan: dict[str, Any], output_root: Path, codex: str) -> dict[str, Any]:
    destination = output_root / cell["cell"]
    destination.mkdir()
    events = destination / "events.jsonl"
    stderr = destination / "stderr.log"
    last_message = destination / "last-message.txt"
    command = [
        codex, "exec", "-m", plan["model"], "-c",
        f'model_reasoning_effort="{plan["reasoning_effort"]}"',
        "--ignore-user-config", "--ignore-rules",
        "--disable", "browser_use", "--disable", "browser_use_external",
        "--disable", "in_app_browser", "--disable", "standalone_web_search",
        "--ephemeral", "--sandbox", "workspace-write", "--skip-git-repo-check",
        "--color", "never", "--json", "-o", str(last_message),
        "-C", str(cell["workspace"]), "-",
    ]
    timed_out = False
    returncode: int | None = None
    with events.open("wb") as stdout_handle, stderr.open("wb") as stderr_handle:
        try:
            completed = subprocess.run(
                command,
                cwd=cell["workspace"],
                env=os.environ.copy(),
                input=plan["system_prompt"].encode("utf-8"),
                stdout=stdout_handle,
                stderr=stderr_handle,
                timeout=plan["timeout_seconds"],
                check=False,
            )
            returncode = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
    event_summary = _event_summary(events)
    response_path = cell["workspace"] / "outbox" / "route-response.json"
    response: dict[str, Any] | None = None
    response_error: str | None = None
    if response_path.is_file() and response_path.stat().st_size <= 1024:
        try:
            parsed = json.loads(response_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                response = parsed
            else:
                response_error = "response-not-object"
        except (UnicodeDecodeError, json.JSONDecodeError):
            response_error = "response-invalid-json"
    elif response_path.is_file():
        response_error = "response-too-large"
    else:
        response_error = "response-missing"
    files = _workspace_files(cell["workspace"])
    custody_passed = files == ALLOWED_FINAL_FILES
    valid = (
        returncode == 0
        and not timed_out
        and event_summary["turn_completed"]
        and event_summary["usage_complete"]
        and event_summary["web_search_items"] == 0
        and custody_passed
        and response is not None
    )
    return {
        "cell": cell["cell"],
        "returncode": returncode,
        "timed_out": timed_out,
        "valid_execution": valid,
        **event_summary,
        "custody_passed": custody_passed,
        "workspace_files": sorted(files),
        "response": response,
        "response_error": response_error,
        "response_sha256": _sha256(response_path.read_bytes()) if response_path.is_file() else None,
        "events_sha256": _sha256(events.read_bytes()),
        "stderr_sha256": _sha256(stderr.read_bytes()),
        "system_prompt_sha256": plan["system_prompt_sha256"],
    }


def run_shadow(manifest_path: Path, output_root: Path, *, codex: str = "codex") -> dict[str, Any]:
    plan = validate_manifest(manifest_path.resolve())
    output_root = output_root.expanduser().resolve()
    if output_root.exists():
        raise SparkShadowError("output root already exists")
    output_root.mkdir(parents=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(plan["cells"])) as executor:
        futures = [executor.submit(_run_cell, cell, plan, output_root, codex) for cell in plan["cells"]]
        cells = [future.result() for future in futures]
    result = {
        "schema": RESULT_SCHEMA,
        "manifest_sha256": plan["manifest_sha256"],
        "automatic_redispatches": 0,
        "cells": cells,
        "valid_execution_cells": sum(cell["valid_execution"] for cell in cells),
        "status": "pass" if all(cell["valid_execution"] for cell in cells) else "fail",
    }
    destination = output_root / "shadow-result.json"
    temporary = output_root / "shadow-result.json.tmp"
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return result

"""Concurrent, no-retry execution of one frozen local Codex wave."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA = "acrouter-codex-spark-wave-v1"
RESULT_SCHEMA = "acrouter-codex-spark-wave-result-v1"
SUPPORTED_MODELS = {"gpt-5.3-codex-spark", "gpt-5.6-sol", "gpt-5.6-luna"}
SUPPORTED_REASONING_EFFORTS = {
    "gpt-5.3-codex-spark": {"low", "medium", "high", "xhigh"},
    "gpt-5.6-sol": {"low", "medium", "high", "xhigh"},
    "gpt-5.6-luna": {"low", "medium", "high", "xhigh", "max"},
}


class SparkWaveError(RuntimeError):
    """A frozen Spark wave manifest or execution boundary is invalid."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SparkWaveError("wave manifest must be a JSON object")
    return value


def _required_text(path: str, digest: str, where: str) -> tuple[Path, str]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise SparkWaveError(f"{where} is missing")
    raw = resolved.read_bytes()
    if _sha256_bytes(raw) != digest:
        raise SparkWaveError(f"{where} digest differs")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SparkWaveError(f"{where} is not UTF-8") from error
    return resolved, text


def validate_manifest(path: Path) -> dict[str, Any]:
    """Validate identities and return a resolved, immutable execution view."""
    value = _load_json(path)
    if value.get("schema") != MANIFEST_SCHEMA:
        raise SparkWaveError("unsupported wave manifest schema")
    if value.get("automatic_redispatch") is not False:
        raise SparkWaveError("automatic_redispatch must be false")
    model = value.get("model")
    if model not in SUPPORTED_MODELS:
        raise SparkWaveError("unsupported local Codex wave model")
    effort = value.get("reasoning_effort")
    if effort not in SUPPORTED_REASONING_EFFORTS[model]:
        raise SparkWaveError("unsupported local Codex wave reasoning effort")
    timeout = value.get("timeout_seconds")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise SparkWaveError("timeout_seconds must be a positive integer")
    raw_cells = value.get("cells")
    if not isinstance(raw_cells, list) or not raw_cells:
        raise SparkWaveError("cells must be a non-empty list")

    cells: list[dict[str, Any]] = []
    ids: set[str] = set()
    workspaces: set[Path] = set()
    for index, raw in enumerate(raw_cells):
        if not isinstance(raw, dict):
            raise SparkWaveError(f"cells[{index}] must be an object")
        expected = {
            "cell", "workspace", "profile", "profile_sha256", "task",
            "task_sha256", "environment_bin",
        }
        if set(raw) != expected:
            raise SparkWaveError(f"cells[{index}] fields differ")
        cell = raw["cell"]
        if not isinstance(cell, str) or not cell or cell in ids or "/" in cell:
            raise SparkWaveError(f"cells[{index}].cell must be a unique safe id")
        workspace = Path(raw["workspace"]).expanduser().resolve()
        environment_bin = Path(raw["environment_bin"]).expanduser().resolve()
        if not workspace.is_dir() or workspace in workspaces:
            raise SparkWaveError(f"cells[{index}].workspace is missing or duplicated")
        if not (environment_bin / "python").is_file():
            raise SparkWaveError(f"cells[{index}].environment_bin has no python")
        profile, profile_text = _required_text(
            raw["profile"], raw["profile_sha256"], f"cells[{index}].profile",
        )
        task, task_text = _required_text(
            raw["task"], raw["task_sha256"], f"cells[{index}].task",
        )
        ids.add(cell)
        workspaces.add(workspace)
        cells.append({
            "cell": cell,
            "workspace": workspace,
            "profile": profile,
            "task": task,
            "profile_text": profile_text,
            "task_text": task_text,
            "environment_bin": environment_bin,
        })
    return {
        "model": model,
        "reasoning_effort": effort,
        "timeout_seconds": timeout,
        "cells": cells,
        "manifest_sha256": _sha256_file(path),
    }


def _event_summary(events_path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    try:
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {
            "events_parseable": False,
            "turn_completed": False,
            "usage_complete": False,
            "web_search_items": 0,
            "usage": None,
            "turn_error": "events-unparseable",
        }
    completed = [row for row in rows if row.get("type") == "turn.completed"]
    failed = [row for row in rows if row.get("type") == "turn.failed"]
    usage = completed[0].get("usage") if len(completed) == 1 else None
    required_usage = {
        "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
        "output_tokens", "reasoning_output_tokens",
    }
    usage_complete = (
        isinstance(usage, dict)
        and set(usage) >= required_usage
        and all(isinstance(usage[key], int) and usage[key] >= 0 for key in required_usage)
    )
    web_search_items = sum(
        row.get("type") in {"item.started", "item.completed"}
        and row.get("item", {}).get("type") == "web_search"
        for row in rows
    )
    turn_error = None
    if failed:
        turn_error = failed[-1].get("error", {}).get("message", "turn-failed")
    return {
        "events_parseable": True,
        "turn_completed": len(completed) == 1,
        "usage_complete": usage_complete,
        "web_search_items": web_search_items,
        "usage": usage if usage_complete else None,
        "turn_error": turn_error,
    }


def _run_cell(
    cell: dict[str, Any],
    *,
    model: str,
    effort: str,
    timeout_seconds: int,
    output_root: Path,
    codex: str,
) -> dict[str, Any]:
    destination = output_root / cell["cell"]
    destination.mkdir()
    events = destination / "events.jsonl"
    stderr = destination / "stderr.log"
    last_message = destination / "last-message.txt"
    prompt = cell["profile_text"] + "\n\n--- Task ---\n\n" + cell["task_text"]
    command = [
        codex,
        "exec",
        "-m",
        model,
        "-c",
        f'model_reasoning_effort="{effort}"',
        "--ignore-user-config",
        "--ignore-rules",
        "--disable",
        "browser_use",
        "--disable",
        "browser_use_external",
        "--disable",
        "in_app_browser",
        "--disable",
        "standalone_web_search",
        "--ephemeral",
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        "--color",
        "never",
        "--json",
        "-o",
        str(last_message),
        "-C",
        str(cell["workspace"]),
        "-",
    ]
    environment = os.environ.copy()
    environment.update({
        "PATH": f"{cell['environment_bin']}:{environment.get('PATH', '')}",
        "PIP_NO_INDEX": "1",
        "PIP_REQUIRE_VIRTUALENV": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    timed_out = False
    returncode: int | None = None
    with events.open("wb") as stdout_handle, stderr.open("wb") as stderr_handle:
        try:
            completed = subprocess.run(
                command,
                cwd=cell["workspace"],
                env=environment,
                input=prompt.encode("utf-8"),
                stdout=stdout_handle,
                stderr=stderr_handle,
                timeout=timeout_seconds,
                check=False,
            )
            returncode = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
    summary = _event_summary(events)
    valid = (
        returncode == 0
        and not timed_out
        and summary["turn_completed"]
        and summary["usage_complete"]
        and summary["web_search_items"] == 0
    )
    return {
        "cell": cell["cell"],
        "returncode": returncode,
        "timed_out": timed_out,
        "valid_execution": valid,
        **summary,
        "events_sha256": _sha256_file(events),
        "stderr_sha256": _sha256_file(stderr),
        "last_message_sha256": _sha256_file(last_message) if last_message.is_file() else None,
        "prompt_sha256": _sha256_bytes(prompt.encode("utf-8")),
    }


def run_wave(manifest_path: Path, output_root: Path, *, codex: str = "codex") -> dict[str, Any]:
    """Execute every frozen cell once and preserve one aggregate result."""
    plan = validate_manifest(manifest_path.resolve())
    output_root = output_root.expanduser().resolve()
    if output_root.exists():
        raise SparkWaveError("output root already exists")
    output_root.mkdir(parents=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(plan["cells"])) as executor:
        futures = [
            executor.submit(
                _run_cell,
                cell,
                model=plan["model"],
                effort=plan["reasoning_effort"],
                timeout_seconds=plan["timeout_seconds"],
                output_root=output_root,
                codex=codex,
            )
            for cell in plan["cells"]
        ]
        cells = [future.result() for future in futures]
    result = {
        "schema": RESULT_SCHEMA,
        "manifest_sha256": plan["manifest_sha256"],
        "automatic_redispatches": 0,
        "cells": cells,
        "valid_execution_cells": sum(cell["valid_execution"] for cell in cells),
        "status": "pass" if all(cell["valid_execution"] for cell in cells) else "fail",
    }
    temporary = output_root / "wave-result.json.tmp"
    destination = output_root / "wave-result.json"
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return result

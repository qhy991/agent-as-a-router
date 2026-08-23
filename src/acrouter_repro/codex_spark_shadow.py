"""No-retry local Codex execution for bounded Router shadow cells."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from .codex_spark_wave import SUPPORTED_REASONING_EFFORTS, _event_summary


MANIFEST_SCHEMAS = {
    "acrouter-codex-shadow-v1",
    "acrouter-codex-spark-shadow-v1",
}
RESULT_SCHEMA = "acrouter-codex-shadow-result-v1"
ALLOWED_INITIAL_FILES = {"inbox/task.md"}
ALLOWED_FINAL_FILES = {"inbox/task.md", "outbox/route-response.json"}
PROFILE_MECHANISM_CONTRACT_KEYS = {
    "schema",
    "stages",
    "allowed_profiles",
    "allowed_mechanism_ids",
    "require_evidence_ref_for_mechanism",
}
PROFILE_MECHANISM_OPTIONAL_CONTRACT_KEYS = {
    "allowed_evidence_refs",
    "require_mechanism_for_dispatch",
}
PROFILE_MECHANISM_ROUTE_KEYS = {
    "stage",
    "decision",
    "profile",
    "mechanism_id",
    "evidence_ref",
}
TASK_FEATURE_CONTRACT_KEYS = {
    "schema",
    "stages",
    "allowed_semantic_kinds",
    "allowed_performance_objectives",
    "minimum_reuse_batches",
    "maximum_reuse_batches",
}
TASK_FEATURE_KEYS = {
    "stage",
    "semantic_kind",
    "reuse_batches",
    "performance_objective",
}


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


def _validate_profile_mechanism_contract(value: Any) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or not PROFILE_MECHANISM_CONTRACT_KEYS <= set(value)
        or set(value) - PROFILE_MECHANISM_CONTRACT_KEYS
        > PROFILE_MECHANISM_OPTIONAL_CONTRACT_KEYS
    ):
        raise SparkShadowError("response_contract fields differ")
    schema = value["schema"]
    if not isinstance(schema, str) or not schema:
        raise SparkShadowError("response_contract.schema is invalid")
    for field, allow_empty in (
        ("stages", False),
        ("allowed_profiles", False),
        ("allowed_mechanism_ids", True),
    ):
        items = value[field]
        if (
            not isinstance(items, list)
            or (not allow_empty and not items)
            or not all(isinstance(item, str) and item for item in items)
            or len(set(items)) != len(items)
        ):
            raise SparkShadowError(f"response_contract.{field} is invalid")
    if not isinstance(value["require_evidence_ref_for_mechanism"], bool):
        raise SparkShadowError(
            "response_contract.require_evidence_ref_for_mechanism is invalid"
        )
    allowed_evidence_refs = value.get("allowed_evidence_refs")
    if allowed_evidence_refs is not None and (
        not isinstance(allowed_evidence_refs, list)
        or not allowed_evidence_refs
        or not all(isinstance(item, str) and item for item in allowed_evidence_refs)
        or len(set(allowed_evidence_refs)) != len(allowed_evidence_refs)
    ):
        raise SparkShadowError(
            "response_contract.allowed_evidence_refs is invalid"
        )
    if not isinstance(value.get("require_mechanism_for_dispatch", False), bool):
        raise SparkShadowError(
            "response_contract.require_mechanism_for_dispatch is invalid"
        )
    return value


def validate_profile_mechanism_response(
    response: Any,
    contract: dict[str, Any],
) -> str | None:
    """Return a bounded validation error, or None for an exact route response."""
    if not isinstance(response, dict) or set(response) != {"schema", "routes"}:
        return "response fields differ"
    if response["schema"] != contract["schema"]:
        return "response schema differs"
    routes = response["routes"]
    stages = contract["stages"]
    if not isinstance(routes, list) or len(routes) != len(stages):
        return "response routes differ"
    for index, (route, stage) in enumerate(zip(routes, stages, strict=True)):
        if not isinstance(route, dict) or set(route) != PROFILE_MECHANISM_ROUTE_KEYS:
            return f"routes[{index}] fields differ"
        if route["stage"] != stage:
            return f"routes[{index}].stage differs"
        decision = route["decision"]
        if decision == "abstain":
            if any(
                route[field] is not None
                for field in ("profile", "mechanism_id", "evidence_ref")
            ):
                return f"routes[{index}] abstain payload differs"
            continue
        if decision != "dispatch":
            return f"routes[{index}].decision is invalid"
        if route["profile"] not in contract["allowed_profiles"]:
            return f"routes[{index}].profile is invalid"
        mechanism = route["mechanism_id"]
        if mechanism is not None and mechanism not in contract["allowed_mechanism_ids"]:
            return f"routes[{index}].mechanism_id is invalid"
        if mechanism is None and contract.get("require_mechanism_for_dispatch", False):
            return f"routes[{index}].mechanism_id is required for dispatch"
        evidence_ref = route["evidence_ref"]
        if evidence_ref is not None and (
            not isinstance(evidence_ref, str) or not evidence_ref
        ):
            return f"routes[{index}].evidence_ref is invalid"
        if (
            evidence_ref is not None
            and contract.get("allowed_evidence_refs") is not None
            and evidence_ref not in contract["allowed_evidence_refs"]
        ):
            return f"routes[{index}].evidence_ref is not allowed"
        if (
            mechanism is not None
            and contract["require_evidence_ref_for_mechanism"]
            and evidence_ref is None
        ):
            return f"routes[{index}].evidence_ref is required for a mechanism"
    return None


def _validate_task_feature_contract(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != TASK_FEATURE_CONTRACT_KEYS:
        raise SparkShadowError("task_feature_contract fields differ")
    _nonempty_contract_list = (
        "stages",
        "allowed_semantic_kinds",
        "allowed_performance_objectives",
    )
    if not isinstance(value["schema"], str) or not value["schema"]:
        raise SparkShadowError("task_feature_contract.schema is invalid")
    for field in _nonempty_contract_list:
        items = value[field]
        if (
            not isinstance(items, list)
            or not items
            or not all(isinstance(item, str) and item for item in items)
            or len(set(items)) != len(items)
        ):
            raise SparkShadowError(f"task_feature_contract.{field} is invalid")
    minimum = value["minimum_reuse_batches"]
    maximum = value["maximum_reuse_batches"]
    if (
        not isinstance(minimum, int)
        or isinstance(minimum, bool)
        or minimum < 1
        or not isinstance(maximum, int)
        or isinstance(maximum, bool)
        or maximum < minimum
    ):
        raise SparkShadowError("task_feature_contract reuse range is invalid")
    return value


def validate_task_feature_response(
    response: Any,
    contract: dict[str, Any],
) -> str | None:
    """Return an error for any feature outside a frozen closed vocabulary."""
    if not isinstance(response, dict) or set(response) != {"schema", "features"}:
        return "response fields differ"
    if response["schema"] != contract["schema"]:
        return "response schema differs"
    features = response["features"]
    stages = contract["stages"]
    if not isinstance(features, list) or len(features) != len(stages):
        return "response features differ"
    for index, (feature, stage) in enumerate(zip(features, stages, strict=True)):
        if not isinstance(feature, dict) or set(feature) != TASK_FEATURE_KEYS:
            return f"features[{index}] fields differ"
        if feature["stage"] != stage:
            return f"features[{index}].stage differs"
        if feature["semantic_kind"] not in contract["allowed_semantic_kinds"]:
            return f"features[{index}].semantic_kind is invalid"
        reuse = feature["reuse_batches"]
        if (
            not isinstance(reuse, int)
            or isinstance(reuse, bool)
            or reuse < contract["minimum_reuse_batches"]
            or reuse > contract["maximum_reuse_batches"]
        ):
            return f"features[{index}].reuse_batches is invalid"
        if (
            feature["performance_objective"]
            not in contract["allowed_performance_objectives"]
        ):
            return f"features[{index}].performance_objective is invalid"
    return None


def validate_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") not in MANIFEST_SCHEMAS:
        raise SparkShadowError("unsupported shadow manifest")
    model = value.get("model")
    if model not in SUPPORTED_REASONING_EFFORTS:
        raise SparkShadowError("unsupported local Codex shadow model")
    if value.get("automatic_redispatch") is not False:
        raise SparkShadowError("automatic_redispatch must be false")
    effort = value.get("reasoning_effort")
    if effort not in SUPPORTED_REASONING_EFFORTS[model]:
        raise SparkShadowError("unsupported local Codex shadow reasoning effort")
    timeout = value.get("timeout_seconds")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise SparkShadowError("timeout_seconds must be positive")
    maximum_response_bytes = value.get("maximum_response_bytes", 1024)
    if (
        not isinstance(maximum_response_bytes, int)
        or isinstance(maximum_response_bytes, bool)
        or maximum_response_bytes < 1
        or maximum_response_bytes > 8192
    ):
        raise SparkShadowError("maximum_response_bytes is invalid")
    _, system_prompt = _snapshot(
        value.get("system_prompt", ""),
        value.get("system_prompt_sha256", ""),
        "system_prompt",
    )
    response_contract = value.get("response_contract")
    if response_contract is not None:
        response_contract = _validate_profile_mechanism_contract(response_contract)
    task_feature_contract = value.get("task_feature_contract")
    if task_feature_contract is not None:
        task_feature_contract = _validate_task_feature_contract(task_feature_contract)
    if response_contract is not None and task_feature_contract is not None:
        raise SparkShadowError("response contracts are mutually exclusive")
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
        "response_contract": response_contract,
        "task_feature_contract": task_feature_contract,
        "maximum_response_bytes": maximum_response_bytes,
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
    if (
        response_path.is_file()
        and response_path.stat().st_size <= plan["maximum_response_bytes"]
    ):
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
    if response is not None and plan["response_contract"] is not None:
        response_error = validate_profile_mechanism_response(
            response,
            plan["response_contract"],
        )
    if response is not None and plan["task_feature_contract"] is not None:
        response_error = validate_task_feature_response(
            response,
            plan["task_feature_contract"],
        )
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
        and response_error is None
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

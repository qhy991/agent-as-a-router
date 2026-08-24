#!/usr/bin/env python3
"""Validate two outcome-blind Agent-as-Router decisions for Connectivity P1f."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


SCHEMA = "modus-connectivity-p1f-router-decision-v1"


def _usage_tokens(usage: dict) -> int | None:
    if not isinstance(usage, dict):
        return None
    if not all(isinstance(usage.get(key), int) for key in ("input_tokens", "output_tokens")):
        return None
    return usage["input_tokens"] + usage["output_tokens"]


def _parse_decision(text: str, task_ids: list[str], actions: list[str]) -> dict:
    value = json.loads(text)
    if not isinstance(value, dict) or set(value) != {"schema", "routes"}:
        raise ValueError("Router response fields differ")
    if value["schema"] != SCHEMA or not isinstance(value["routes"], list):
        raise ValueError("Router response schema differs")
    if len(value["routes"]) != len(task_ids):
        raise ValueError("Router response task count differs")
    resolved = {}
    reasons = {}
    for route in value["routes"]:
        if not isinstance(route, dict) or set(route) != {"task_id", "action", "reason"}:
            raise ValueError("Router route fields differ")
        task_id = route["task_id"]
        action = route["action"]
        reason = route["reason"]
        if task_id not in task_ids or task_id in resolved:
            raise ValueError("Router route task is unsupported or duplicated")
        if action not in actions:
            raise ValueError("Router action is unsupported")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Router reason is empty")
        resolved[task_id] = action
        reasons[task_id] = reason.strip()
    if set(resolved) != set(task_ids):
        raise ValueError("Router response omits a task")
    return {"actions_by_task": resolved, "reasons_by_task": reasons}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args(argv)

    root = options.run_root.resolve()
    protocol = json.loads(options.protocol.read_text(encoding="utf-8"))
    wave = json.loads((root / "output" / "wave-result.json").read_text())
    task_ids = list(protocol["tasks"])
    allowed_actions = protocol["router"]["allowed_actions"]
    decisions = []
    cells = []
    for cell in wave["cells"]:
        message_path = root / "output" / cell["cell"] / "last-message.txt"
        parsed = None
        error = None
        if cell["valid_execution"] and message_path.is_file():
            try:
                parsed = _parse_decision(
                    message_path.read_text(encoding="utf-8"), task_ids, allowed_actions
                )
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as caught:
                error = str(caught)
        else:
            error = "invalid execution or missing final message"
        if parsed:
            decisions.append(parsed["actions_by_task"])
        cells.append({
            "cell": cell["cell"],
            "valid_execution": cell["valid_execution"],
            "parsed": parsed,
            "parse_error": error,
            "usage": cell.get("usage"),
            "total_tokens": _usage_tokens(cell.get("usage")),
            "last_message_sha256": cell.get("last_message_sha256"),
        })
    stable = (
        len(decisions) == protocol["router"]["repetitions"]
        and all(decision == decisions[0] for decision in decisions)
    )
    usage = [cell["total_tokens"] for cell in cells]
    complete_usage = all(value is not None for value in usage)
    authorized = bool(stable and complete_usage and wave.get("status") == "pass")
    report = {
        "schema": "modus-connectivity-p1f-router-validation-v1",
        "status": "pass" if authorized else "fail",
        "cells": cells,
        "stable_actions_by_task": decisions[0] if stable else None,
        "stable_repetitions": len(decisions) if stable else 0,
        "router_acquisition_tokens": sum(usage) if complete_usage else None,
        "router_tokens_per_deployment": statistics.median(usage) if complete_usage else None,
        "worker_protocol_authorized": authorized,
        "decision": "freeze_selected_worker_protocol" if authorized else "stop_without_workers",
    }
    options.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "stable_actions": report["stable_actions_by_task"],
        "router_acquisition_tokens": report["router_acquisition_tokens"],
        "router_tokens_per_deployment": report["router_tokens_per_deployment"],
        "decision": report["decision"],
    }, sort_keys=True))
    return 0 if authorized else 2


if __name__ == "__main__":
    raise SystemExit(main())

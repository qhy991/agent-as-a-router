#!/usr/bin/env python3
"""Validate one outcome-blind P2s three-task Profile route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "modus-performance-p2s-router-decision-v1"


def _parse(text: str, tasks: list[str], actions: list[str]) -> dict:
    value = json.loads(text)
    if not isinstance(value, dict) or set(value) != {"schema", "routes"}:
        raise ValueError("Router response fields differ")
    if value["schema"] != SCHEMA or not isinstance(value["routes"], list):
        raise ValueError("Router response schema differs")
    resolved, reasons = {}, {}
    for row in value["routes"]:
        if not isinstance(row, dict) or set(row) != {"task", "action", "reason"}:
            raise ValueError("Router route fields differ")
        task, action, reason = row["task"], row["action"], row["reason"]
        if task not in tasks or task in resolved:
            raise ValueError("Router task is unsupported or duplicated")
        if action not in actions:
            raise ValueError("Router action is unsupported")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Router reason is empty")
        resolved[task] = action
        reasons[task] = reason.strip()
    if set(resolved) != set(tasks):
        raise ValueError("Router response omits a task")
    return {"actions_by_task": resolved, "reasons_by_task": reasons}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.run_root.resolve(); protocol = json.loads(args.protocol.read_text())
    wave = json.loads((root / "output/wave-result.json").read_text())
    cell = wave["cells"][0]
    message = root / "output" / cell["cell"] / "last-message.txt"
    parsed, error = None, None
    try:
        if not cell["valid_execution"] or not message.is_file():
            raise ValueError("invalid execution or missing final message")
        parsed = _parse(message.read_text(), protocol["router"]["tasks"], protocol["router"]["allowed_actions"])
    except (OSError, json.JSONDecodeError, ValueError) as caught:
        error = str(caught)
    usage = cell.get("usage")
    total = usage["input_tokens"] + usage["output_tokens"] if isinstance(usage, dict) else None
    valid = parsed is not None and total is not None and wave["status"] == "pass"
    report = {
        "schema": "modus-performance-p2s-router-validation-v1",
        "status": "pass" if valid else "fail",
        "parsed": parsed,
        "parse_error": error,
        "usage": usage,
        "router_tokens": total,
        "worker_matrix_authorized": valid,
        "worker_deployment_authorized": False,
        "last_message_sha256": cell.get("last_message_sha256"),
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "actions": parsed["actions_by_task"] if parsed else None, "router_tokens": total, "worker_deployment_authorized": False}, sort_keys=True))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())

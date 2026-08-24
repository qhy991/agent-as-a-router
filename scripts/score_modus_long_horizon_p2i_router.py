#!/usr/bin/env python3
"""Validate one outcome-blind P2i Agent qualification proposal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "modus-long-horizon-p2i-router-decision-v1"


def _usage_tokens(usage: dict) -> int | None:
    if not isinstance(usage, dict):
        return None
    if not all(isinstance(usage.get(key), int) for key in ("input_tokens", "output_tokens")):
        return None
    return usage["input_tokens"] + usage["output_tokens"]


def _parse_decision(text: str, stages: list[str], actions: list[str]) -> dict:
    value = json.loads(text)
    if not isinstance(value, dict) or set(value) != {"schema", "routes"}:
        raise ValueError("Router response fields differ")
    if value["schema"] != SCHEMA or not isinstance(value["routes"], list):
        raise ValueError("Router response schema differs")
    resolved: dict[str, str] = {}
    reasons: dict[str, str] = {}
    for route in value["routes"]:
        if not isinstance(route, dict) or set(route) != {"stage", "action", "reason"}:
            raise ValueError("Router route fields differ")
        stage, action, reason = route["stage"], route["action"], route["reason"]
        if stage not in stages or stage in resolved:
            raise ValueError("Router stage is unsupported or duplicated")
        if action not in actions:
            raise ValueError("Router action is unsupported")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Router reason is empty")
        resolved[stage] = action
        reasons[stage] = reason.strip()
    if set(resolved) != set(stages):
        raise ValueError("Router response omits a stage")
    return {"actions_by_stage": resolved, "reasons_by_stage": reasons}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args(argv)
    root = options.run_root.resolve()
    protocol = json.loads(options.protocol.read_text(encoding="utf-8"))
    wave = json.loads((root / "output" / "wave-result.json").read_text())
    stages = protocol["router"]["stages"]
    actions = protocol["router"]["allowed_actions"]
    cells: list[dict] = []
    decisions: list[dict[str, str]] = []
    for cell in wave["cells"]:
        path = root / "output" / cell["cell"] / "last-message.txt"
        parsed, error = None, None
        try:
            if not cell["valid_execution"] or not path.is_file():
                raise ValueError("invalid execution or missing final message")
            parsed = _parse_decision(path.read_text(encoding="utf-8"), stages, actions)
            decisions.append(parsed["actions_by_stage"])
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as caught:
            error = str(caught)
        cells.append({
            "cell": cell["cell"],
            "valid_execution": cell["valid_execution"],
            "parsed": parsed,
            "parse_error": error,
            "usage": cell.get("usage"),
            "total_tokens": _usage_tokens(cell.get("usage")),
            "last_message_sha256": cell.get("last_message_sha256"),
        })
    usage = [cell["total_tokens"] for cell in cells]
    authorized = (
        wave.get("status") == "pass"
        and len(decisions) == protocol["router"]["repetitions"] == 1
        and all(value is not None for value in usage)
    )
    report = {
        "schema": "modus-long-horizon-p2i-router-validation-v1",
        "status": "pass" if authorized else "fail",
        "cells": cells,
        "proposed_actions_by_stage": decisions[0] if authorized else None,
        "router_acquisition_tokens": sum(usage) if all(value is not None for value in usage) else None,
        "worker_deployment_authorized": False,
        "qualification_pair_protocol_authorized": authorized,
        "decision": "freeze_qualification_pair" if authorized else "stop",
    }
    options.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "proposed_actions": report["proposed_actions_by_stage"],
        "router_acquisition_tokens": report["router_acquisition_tokens"],
        "worker_deployment_authorized": False,
        "decision": report["decision"],
    }, sort_keys=True))
    return 0 if authorized else 2


if __name__ == "__main__":
    raise SystemExit(main())

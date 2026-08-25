#!/usr/bin/env python3
"""Validate one evidence-grounded formal Modus Router decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "modus-router-batch-decision-v1"


def parse_response(text: str, protocol: dict) -> dict:
    value = json.loads(text)
    if not isinstance(value, dict) or set(value) != {"schema", "routes"}:
        raise ValueError("Router response fields differ")
    if value["schema"] != SCHEMA or not isinstance(value["routes"], list):
        raise ValueError("Router response schema differs")
    tasks = protocol["router"]["tasks"]
    allowed = set(protocol["strategies"])
    supported = protocol["router"]["qualified_dispatch"]
    if len(value["routes"]) != len(tasks):
        raise ValueError("Router route count differs")
    parsed = []
    for index, (route, task_id) in enumerate(zip(value["routes"], tasks, strict=True)):
        if not isinstance(route, dict) or set(route) != {
            "task_id", "decision", "strategy", "evidence_refs", "reason"
        }:
            raise ValueError(f"routes[{index}] fields differ")
        if route["task_id"] != task_id:
            raise ValueError(f"routes[{index}].task_id differs")
        decision = route["decision"]
        if decision not in {"dispatch", "abstain", "request_qualification"}:
            raise ValueError(f"routes[{index}].decision differs")
        if not isinstance(route["reason"], str) or not route["reason"].strip():
            raise ValueError(f"routes[{index}].reason is empty")
        strategy = route["strategy"]
        evidence_refs = route["evidence_refs"]
        if not isinstance(evidence_refs, list) or not all(
            isinstance(item, str) and item for item in evidence_refs
        ):
            raise ValueError(f"routes[{index}].evidence_refs are invalid")
        if decision == "dispatch":
            qualified = supported[task_id]
            if strategy != qualified["strategy"]:
                raise ValueError(f"routes[{index}] dispatch strategy is not qualified")
            if evidence_refs != [qualified["evidence_ref"]]:
                raise ValueError(f"routes[{index}] dispatch evidence differs")
        else:
            if strategy is not None or evidence_refs:
                raise ValueError(f"routes[{index}] non-dispatch fields differ")
        if strategy is not None and strategy not in allowed:
            raise ValueError(f"routes[{index}].strategy is unsupported")
        parsed.append({
            "task_id": task_id,
            "decision": decision,
            "strategy": strategy,
            "evidence_refs": evidence_refs,
            "reason": route["reason"].strip(),
        })
    return {"routes": parsed}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.run_root.resolve()
    protocol = json.loads(args.protocol.read_text())
    wave = json.loads((root / "output/wave-result.json").read_text())
    cell = wave["cells"][0]
    message = root / "output" / cell["cell"] / "last-message.txt"
    parsed = None
    error = None
    try:
        if not cell["valid_execution"] or not message.is_file():
            raise ValueError("invalid execution or missing final message")
        parsed = parse_response(message.read_text(), protocol)
    except (OSError, json.JSONDecodeError, ValueError) as caught:
        error = str(caught)
    usage = cell.get("usage")
    total = (
        usage["input_tokens"] + usage["output_tokens"]
        if isinstance(usage, dict) else None
    )
    valid = parsed is not None and total is not None and wave["status"] == "pass"
    requests = (
        sum(row["decision"] == "request_qualification" for row in parsed["routes"])
        if parsed else None
    )
    report = {
        "schema": "modus-profile-experience-router-validation-v1",
        "status": "pass" if valid else "fail",
        "parsed": parsed,
        "parse_error": error,
        "usage": usage,
        "router_tokens": total,
        "qualification_requests": requests,
        "worker_acquisition_authorized": valid and requests == 0,
        "worker_deployment_authorized": False,
        "last_message_sha256": cell.get("last_message_sha256"),
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "routes": parsed["routes"] if parsed else None,
        "router_tokens": total,
        "worker_acquisition_authorized": report["worker_acquisition_authorized"],
    }, sort_keys=True))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())

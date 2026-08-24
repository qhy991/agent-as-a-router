"""Resolve one pending Modus qualification request from a derived candidate view."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def resolve_qualification_request(
    request: dict[str, Any], candidate_view: dict[str, Any],
) -> dict[str, Any]:
    required = {
        "candidate_view_sha256", "reason", "request_id", "response_sha256",
        "stage", "typed_descriptor",
    }
    if not isinstance(request, dict) or set(request) != required:
        raise ValueError("qualification request fields differ")
    if not isinstance(candidate_view, dict):
        raise ValueError("qualification candidate view is invalid")
    stages = candidate_view.get("stages")
    if candidate_view.get("schema") != "modus-derived-qualified-candidate-view-v1" or not isinstance(stages, list) or len(stages) != 1:
        raise ValueError("qualification candidate view is invalid")
    row = stages[0]
    if row.get("stage") != request["stage"] or row.get("descriptor") != request["typed_descriptor"]:
        raise ValueError("qualification request and candidate descriptor differ")
    resolution = row.get("resolution")
    if not isinstance(resolution, dict):
        raise ValueError("qualification resolution is invalid")
    result = {
        "schema": "modus-qualification-request-resolution-v1",
        "request_id": request["request_id"],
        "stage": request["stage"],
        "request_sha256": _sha(request),
        "candidate_view_sha256": _sha(candidate_view),
        "neutral_fallbacks": 0,
    }
    if resolution.get("decision") != "dispatch":
        return {**result, "status": "pending", "worker_dispatch": None}
    action = resolution.get("action")
    if not isinstance(action, dict) or set(action) != {"profile", "mechanism_id", "evidence_ref"}:
        raise ValueError("qualification dispatch action is invalid")
    return {
        **result,
        "status": "accepted",
        "worker_dispatch": {"stage": request["stage"], **action},
    }

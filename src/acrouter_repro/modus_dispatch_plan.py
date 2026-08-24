"""Derive a fail-closed manager plan from validated Modus Agent routes."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .codex_spark_shadow import (
    _validate_profile_mechanism_contract,
    validate_profile_mechanism_response,
)


VIEW_SCHEMA = "modus-derived-qualified-candidate-view-v1"
PLAN_SCHEMA = "modus-manager-dispatch-plan-v1"


class DispatchPlanError(ValueError):
    """The response and candidate view cannot produce a safe manager plan."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def build_dispatch_plan(
    *, response: dict[str, Any], contract: dict[str, Any],
    candidate_view: dict[str, Any], response_sha256: str,
    candidate_view_sha256: str,
) -> dict[str, Any]:
    try:
        contract = _validate_profile_mechanism_contract(contract)
    except Exception as error:
        raise DispatchPlanError("response contract is invalid") from error
    validation = validate_profile_mechanism_response(response, contract)
    if validation is not None:
        raise DispatchPlanError(f"Agent response is invalid: {validation}")
    if (
        not isinstance(candidate_view, dict)
        or candidate_view.get("schema") != VIEW_SCHEMA
        or not isinstance(candidate_view.get("stages"), list)
    ):
        raise DispatchPlanError("candidate view is invalid")
    view_rows = candidate_view["stages"]
    routes = response["routes"]
    if len(view_rows) != len(routes) or len(routes) != len(contract["stages"]):
        raise DispatchPlanError("stage counts differ")
    dispatches = []
    requests = []
    for index, (view, route, expected_stage) in enumerate(
        zip(view_rows, routes, contract["stages"], strict=True)
    ):
        if not isinstance(view, dict) or set(view) != {"stage", "descriptor", "resolution"}:
            raise DispatchPlanError(f"candidate view stage {index} fields differ")
        stage = view["stage"]
        if stage != expected_stage or route["stage"] != stage:
            raise DispatchPlanError(f"stage {index} identity differs")
        resolution = view["resolution"]
        if not isinstance(resolution, dict) or resolution.get("decision") not in {
            "dispatch", "abstain",
        }:
            raise DispatchPlanError(f"stage {index} resolution is invalid")
        if route["decision"] == "dispatch":
            action = resolution.get("action")
            if (
                resolution["decision"] != "dispatch"
                or not isinstance(action, dict)
                or set(action) != {"profile", "mechanism_id", "evidence_ref"}
                or route["profile"] != action["profile"]
                or route["mechanism_id"] != action["mechanism_id"]
                or route["evidence_ref"] != action["evidence_ref"]
            ):
                raise DispatchPlanError(f"stage {index} dispatch differs from candidate")
            dispatches.append({
                "stage": stage,
                "profile": action["profile"],
                "mechanism_id": action["mechanism_id"],
                "evidence_ref": action["evidence_ref"],
            })
            continue
        if route["decision"] != "abstain":
            raise DispatchPlanError(f"stage {index} decision is unsupported")
        reason = resolution.get("reason")
        if not isinstance(reason, str) or not reason:
            raise DispatchPlanError(f"stage {index} abstain reason is missing")
        descriptor = view["descriptor"]
        request_payload = {
            "stage": stage,
            "typed_descriptor": descriptor,
            "reason": reason,
            "response_sha256": response_sha256,
            "candidate_view_sha256": candidate_view_sha256,
        }
        requests.append({
            **request_payload,
            "request_id": "qualification:" + _sha(request_payload),
        })
    if requests and dispatches:
        status = "partial_pending_qualification"
    elif requests:
        status = "deferred_pending_qualification"
    else:
        status = "complete"
    return {
        "schema": PLAN_SCHEMA,
        "status": status,
        "complete": status == "complete",
        "neutral_fallbacks": 0,
        "worker_dispatches": dispatches,
        "qualification_requests": requests,
        "source": {
            "response_sha256": response_sha256,
            "candidate_view_sha256": candidate_view_sha256,
            "response_contract_sha256": _sha(contract),
        },
    }

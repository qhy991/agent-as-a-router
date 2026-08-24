"""Outcome qualification envelope for exact Modus route cache entries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .modus_route_cache import load_cached_route, sha256_value


SCHEMA = "modus-route-qualification-envelope-v1"
FIELDS = {
    "schema", "status", "route_entry_path", "route_entry_sha256",
    "decision_sha256", "route_actions", "outcome_evidence_path",
    "outcome_evidence_sha256", "policy", "observed",
}
POLICY_FIELDS = {
    "performance_ratio_maximum", "relative_mad_maximum",
    "minimum_token_saving_fraction",
}
OBSERVED_FIELDS = {
    "correctness_passed", "performance_ratio", "maximum_relative_mad",
    "token_saving_fraction", "evidence_stable",
}


class RouteQualificationError(ValueError):
    """A cached route is not qualified for deployment."""


def _digest(value: Any, where: str) -> str:
    if (
        not isinstance(value, str) or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{where} must be a lowercase sha256")
    return value


def validate_policy(value: Any) -> dict[str, float]:
    if not isinstance(value, dict) or set(value) != POLICY_FIELDS:
        raise ValueError("qualification policy fields differ")
    for field, number in value.items():
        if not isinstance(number, (int, float)) or isinstance(number, bool) or number < 0:
            raise ValueError(f"qualification policy {field} is invalid")
    if value["performance_ratio_maximum"] < 1.0:
        raise ValueError("performance ratio maximum must be at least one")
    if value["minimum_token_saving_fraction"] > 1.0:
        raise ValueError("minimum token saving fraction exceeds one")
    return value


def validate_observed(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != OBSERVED_FIELDS:
        raise ValueError("qualification observed fields differ")
    for field in ("correctness_passed", "evidence_stable"):
        if not isinstance(value[field], bool):
            raise ValueError(f"qualification observed {field} is invalid")
    for field in ("performance_ratio", "maximum_relative_mad", "token_saving_fraction"):
        number = value[field]
        if not isinstance(number, (int, float)) or isinstance(number, bool):
            raise ValueError(f"qualification observed {field} is invalid")
    if value["performance_ratio"] < 0 or value["maximum_relative_mad"] < 0:
        raise ValueError("qualification observed performance or noise is negative")
    return value


def qualification_status(policy: dict[str, float], observed: dict[str, Any]) -> str:
    policy = validate_policy(policy)
    observed = validate_observed(observed)
    passed = all((
        observed["correctness_passed"],
        observed["evidence_stable"],
        observed["performance_ratio"] <= policy["performance_ratio_maximum"],
        observed["maximum_relative_mad"] <= policy["relative_mad_maximum"],
        observed["token_saving_fraction"] >= policy["minimum_token_saving_fraction"],
    ))
    return "qualified" if passed else "rejected"


def build_envelope(
    *, route_entry_path: str, route_entry: dict[str, Any],
    route_entry_sha256: str, outcome_evidence_path: str,
    outcome_evidence_sha256: str, policy: dict[str, float],
    observed: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(route_entry_path, str) or not route_entry_path:
        raise ValueError("route entry path is invalid")
    if not isinstance(outcome_evidence_path, str) or not outcome_evidence_path:
        raise ValueError("outcome evidence path is invalid")
    _digest(route_entry_sha256, "route_entry_sha256")
    _digest(outcome_evidence_sha256, "outcome_evidence_sha256")
    if not isinstance(route_entry, dict):
        raise ValueError("route entry is invalid")
    decision = route_entry.get("decision")
    decision_sha256 = route_entry.get("decision_sha256")
    if not isinstance(decision, dict) or decision_sha256 != sha256_value(decision):
        raise ValueError("route entry decision digest differs")
    actions = decision.get("actions_by_stage")
    if not isinstance(actions, dict) or not actions:
        raise ValueError("route entry actions are invalid")
    policy = validate_policy(policy)
    observed = validate_observed(observed)
    return {
        "schema": SCHEMA,
        "status": qualification_status(policy, observed),
        "route_entry_path": route_entry_path,
        "route_entry_sha256": route_entry_sha256,
        "decision_sha256": decision_sha256,
        "route_actions": actions,
        "outcome_evidence_path": outcome_evidence_path,
        "outcome_evidence_sha256": outcome_evidence_sha256,
        "policy": policy,
        "observed": observed,
    }


def load_qualified_cached_route(
    *, entry_path: Path, current_key: dict[str, Any], envelope_path: Path,
    evidence_root: Path, current_policy: dict[str, float],
) -> dict[str, Any]:
    cached = load_cached_route(
        entry_path, current_key=current_key, evidence_root=evidence_root,
    )
    try:
        envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
        if not isinstance(envelope, dict) or set(envelope) != FIELDS:
            raise ValueError("qualification envelope fields differ")
        if envelope["schema"] != SCHEMA:
            raise ValueError("qualification envelope schema differs")
        policy = validate_policy(envelope["policy"])
        current_policy = validate_policy(current_policy)
        if policy != current_policy:
            raise ValueError("current qualification policy differs")
        observed = validate_observed(envelope["observed"])
        recomputed = qualification_status(policy, observed)
        if envelope["status"] != recomputed:
            raise ValueError("qualification status differs from observed evidence")
        if envelope["status"] != "qualified":
            raise ValueError("cached route is not outcome-qualified")
        if envelope["route_entry_sha256"] != hashlib.sha256(entry_path.read_bytes()).hexdigest():
            raise ValueError("qualified route entry digest differs")
        entry = json.loads(entry_path.read_text(encoding="utf-8"))
        if envelope["decision_sha256"] != entry.get("decision_sha256"):
            raise ValueError("qualified decision digest differs")
        if envelope["route_actions"] != cached["actions_by_stage"]:
            raise ValueError("qualified route actions differ")
        evidence_path = evidence_root / envelope["outcome_evidence_path"]
        if not evidence_path.is_file():
            raise ValueError("qualification outcome evidence is missing")
        if hashlib.sha256(evidence_path.read_bytes()).hexdigest() != envelope["outcome_evidence_sha256"]:
            raise ValueError("qualification outcome evidence digest differs")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RouteQualificationError(str(error)) from error
    return {
        **cached,
        "deployment_qualified": True,
        "qualification_envelope_sha256": hashlib.sha256(envelope_path.read_bytes()).hexdigest(),
    }

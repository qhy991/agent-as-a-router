"""Validate and project accumulated Modus Router experience."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REGISTRY_SCHEMA = "modus-profile-experience-registry-v1"
DESCRIPTOR_SCHEMA = "modus-router-task-descriptor-v1"
CONTEXT_SCHEMA = "modus-router-evidence-context-v1"
BATCH_CONTEXT_SCHEMA = "modus-router-evidence-batch-v1"
DESCRIPTOR_FIELDS = {
    "schema",
    "task_id",
    "worker_model",
    "semantic_kind",
    "workload_shape",
    "reusable_preparation",
    "performance_objective",
}
SIGNATURE_FIELDS = {
    "semantic_kind",
    "workload_shape",
    "reusable_preparation",
    "performance_objective",
}
LEGACY_ROUTER_TERMS = ("p2s", "p2t", "p000", "p100", "e1v2", "e1v3")


class RouterExperienceError(ValueError):
    """A Router policy, registry, descriptor, or evidence projection is invalid."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise RouterExperienceError(f"{where} must be non-empty text")
    return value


def _digest(value: Any, where: str) -> str:
    value = _text(value, where)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise RouterExperienceError(f"{where} must be a lowercase sha256")
    return value


def _validate_model(value: Any, where: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"slug", "reasoning_effort"}:
        raise RouterExperienceError(f"{where} fields differ")
    return {
        "slug": _text(value["slug"], f"{where}.slug"),
        "reasoning_effort": _text(
            value["reasoning_effort"], f"{where}.reasoning_effort"
        ),
    }


def _validate_signature(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != SIGNATURE_FIELDS:
        raise RouterExperienceError(f"{where} fields differ")
    if not isinstance(value["reusable_preparation"], bool):
        raise RouterExperienceError(f"{where}.reusable_preparation must be boolean")
    return {
        "semantic_kind": _text(value["semantic_kind"], f"{where}.semantic_kind"),
        "workload_shape": _text(value["workload_shape"], f"{where}.workload_shape"),
        "reusable_preparation": value["reusable_preparation"],
        "performance_objective": _text(
            value["performance_objective"], f"{where}.performance_objective"
        ),
    }


def load_registry(path: Path) -> dict[str, Any]:
    """Load one hash-bound experience registry and validate referenced evidence."""
    path = path.expanduser().resolve()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RouterExperienceError("experience registry is unreadable") from error
    required = {
        "schema",
        "worker_model",
        "cost_metric",
        "strategies",
        "task_experience",
        "router_experience",
        "decision_policy",
        "claim_boundary",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise RouterExperienceError("experience registry fields differ")
    if value["schema"] != REGISTRY_SCHEMA:
        raise RouterExperienceError("experience registry schema differs")
    model = _validate_model(value["worker_model"], "worker_model")
    _text(value["cost_metric"], "cost_metric")
    _text(value["claim_boundary"], "claim_boundary")
    strategies = value["strategies"]
    if not isinstance(strategies, list) or not strategies:
        raise RouterExperienceError("strategies must be a non-empty list")
    strategy_ids: set[str] = set()
    for index, strategy in enumerate(strategies):
        where = f"strategies[{index}]"
        if not isinstance(strategy, dict) or set(strategy) != {
            "strategy_id", "summary", "behavior_contract", "artifact_sha256"
        }:
            raise RouterExperienceError(f"{where} fields differ")
        strategy_id = _text(strategy["strategy_id"], f"{where}.strategy_id")
        if strategy_id in strategy_ids:
            raise RouterExperienceError("strategy IDs must be unique")
        strategy_ids.add(strategy_id)
        _text(strategy["summary"], f"{where}.summary")
        behavior = strategy["behavior_contract"]
        if not isinstance(behavior, dict) or set(behavior) != {
            "topology", "reusable_preparation"
        }:
            raise RouterExperienceError(f"{where}.behavior_contract fields differ")
        _text(behavior["topology"], f"{where}.behavior_contract.topology")
        _text(
            behavior["reusable_preparation"],
            f"{where}.behavior_contract.reusable_preparation",
        )
        _digest(strategy["artifact_sha256"], f"{where}.artifact_sha256")
    repository = path.parent.parent
    evidence_references: set[str] = set()
    task_experience = value["task_experience"]
    if not isinstance(task_experience, list) or not task_experience:
        raise RouterExperienceError("task_experience must be a non-empty list")
    experience_ids: set[str] = set()
    for index, experience in enumerate(task_experience):
        where = f"task_experience[{index}]"
        if not isinstance(experience, dict) or set(experience) != {
            "experience_id",
            "maturity",
            "task_signature",
            "selected_strategy",
            "observations",
            "rejected_strategies",
            "evidence",
        }:
            raise RouterExperienceError(f"{where} fields differ")
        experience_id = _text(experience["experience_id"], f"{where}.experience_id")
        if experience_id in experience_ids:
            raise RouterExperienceError("experience IDs must be unique")
        experience_ids.add(experience_id)
        _text(experience["maturity"], f"{where}.maturity")
        _validate_signature(experience["task_signature"], f"{where}.task_signature")
        if experience["selected_strategy"] not in strategy_ids:
            raise RouterExperienceError(f"{where}.selected_strategy is unknown")
        observations = experience["observations"]
        required_observations = {
            "correctness_passed",
            "behavior_passed",
            "performance_ratio_to_unconstrained",
            "token_saving_fraction_vs_unconstrained",
            "selected_worker_tokens",
        }
        if not isinstance(observations, dict) or set(observations) != required_observations:
            raise RouterExperienceError(f"{where}.observations fields differ")
        if observations["correctness_passed"] is not True or observations["behavior_passed"] is not True:
            raise RouterExperienceError(f"{where} is not quality-qualified")
        if (
            not isinstance(observations["performance_ratio_to_unconstrained"], (int, float))
            or observations["performance_ratio_to_unconstrained"] <= 0
            or not isinstance(observations["token_saving_fraction_vs_unconstrained"], (int, float))
            or not isinstance(observations["selected_worker_tokens"], int)
            or isinstance(observations["selected_worker_tokens"], bool)
            or observations["selected_worker_tokens"] <= 0
        ):
            raise RouterExperienceError(f"{where}.observations are invalid")
        rejected = experience["rejected_strategies"]
        if not isinstance(rejected, list):
            raise RouterExperienceError(f"{where}.rejected_strategies must be a list")
        for rejected_index, rejection in enumerate(rejected):
            rejection_where = f"{where}.rejected_strategies[{rejected_index}]"
            if not isinstance(rejection, dict) or set(rejection) != {
                "strategy_id",
                "reason",
                "performance_ratio_to_unconstrained",
                "token_saving_fraction_vs_unconstrained",
            }:
                raise RouterExperienceError(f"{rejection_where} fields differ")
            if rejection["strategy_id"] not in strategy_ids:
                raise RouterExperienceError(f"{rejection_where}.strategy_id is unknown")
            _text(rejection["reason"], f"{rejection_where}.reason")
        _validate_evidence(
            experience["evidence"], f"{where}.evidence", repository, evidence_references
        )
    router_experience = value["router_experience"]
    if not isinstance(router_experience, list) or not router_experience:
        raise RouterExperienceError("router_experience must be a non-empty list")
    for index, experience in enumerate(router_experience):
        where = f"router_experience[{index}]"
        if not isinstance(experience, dict) or set(experience) != {
            "experience_id", "maturity", "observation", "evidence"
        }:
            raise RouterExperienceError(f"{where} fields differ")
        experience_id = _text(experience["experience_id"], f"{where}.experience_id")
        if experience_id in experience_ids:
            raise RouterExperienceError("experience IDs must be unique")
        experience_ids.add(experience_id)
        _text(experience["maturity"], f"{where}.maturity")
        if not isinstance(experience["observation"], dict) or not experience["observation"]:
            raise RouterExperienceError(f"{where}.observation is invalid")
        _validate_evidence(
            experience["evidence"], f"{where}.evidence", repository, evidence_references
        )
    policy = value["decision_policy"]
    if not isinstance(policy, dict) or set(policy) != {
        "quality_order",
        "maximum_performance_ratio",
        "maximum_relative_mad",
        "minimum_token_saving_fraction",
        "decisions",
        "exact_cache_before_agent",
        "missing_evidence_decision",
    }:
        raise RouterExperienceError("decision_policy fields differ")
    if policy["decisions"] != ["dispatch", "abstain", "request_qualification"]:
        raise RouterExperienceError("decision_policy decisions differ")
    if policy["missing_evidence_decision"] != "request_qualification":
        raise RouterExperienceError("missing evidence must request qualification")
    value["worker_model"] = model
    return value


def _validate_evidence(
    evidence: Any,
    where: str,
    repository: Path,
    references: set[str],
) -> None:
    if not isinstance(evidence, dict) or set(evidence) != {
        "evidence_ref", "path", "sha256"
    }:
        raise RouterExperienceError(f"{where} fields differ")
    reference = _text(evidence["evidence_ref"], f"{where}.evidence_ref")
    if reference in references:
        raise RouterExperienceError("evidence refs must be unique")
    references.add(reference)
    relative = Path(_text(evidence["path"], f"{where}.path"))
    if relative.is_absolute() or ".." in relative.parts:
        raise RouterExperienceError(f"{where}.path must be repository-relative")
    digest = _digest(evidence["sha256"], f"{where}.sha256")
    artifact = repository / relative
    if not artifact.is_file() or _sha256(artifact) != digest:
        raise RouterExperienceError(f"{where} artifact is missing or changed")


def load_descriptor(path: Path) -> dict[str, Any]:
    """Load one formal Router task descriptor."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RouterExperienceError("task descriptor is unreadable") from error
    if not isinstance(value, dict) or set(value) != DESCRIPTOR_FIELDS:
        raise RouterExperienceError("task descriptor fields differ")
    if value["schema"] != DESCRIPTOR_SCHEMA:
        raise RouterExperienceError("task descriptor schema differs")
    return {
        "schema": DESCRIPTOR_SCHEMA,
        "task_id": _text(value["task_id"], "task_id"),
        "worker_model": _validate_model(value["worker_model"], "worker_model"),
        **_validate_signature(
            {field: value[field] for field in SIGNATURE_FIELDS},
            "task_signature",
        ),
    }


def build_context(
    *, registry: dict[str, Any], descriptor: dict[str, Any],
    policy_path: Path, registry_path: Path,
) -> dict[str, Any]:
    """Build the legacy-free evidence view consumed by the Router Agent."""
    if descriptor["worker_model"] != registry["worker_model"]:
        relevant: list[dict[str, Any]] = []
    else:
        signature = {field: descriptor[field] for field in SIGNATURE_FIELDS}
        relevant = [
            {
                "experience_id": item["experience_id"],
                "maturity": item["maturity"],
                "task_signature": item["task_signature"],
                "selected_strategy": item["selected_strategy"],
                "observations": item["observations"],
                "rejected_strategies": item["rejected_strategies"],
                "evidence_ref": item["evidence"]["evidence_ref"],
            }
            for item in registry["task_experience"]
            if item["task_signature"] == signature
        ]
    context = {
        "schema": CONTEXT_SCHEMA,
        "task": descriptor,
        "strategies": [
            {
                "strategy_id": item["strategy_id"],
                "summary": item["summary"],
                "behavior_contract": item["behavior_contract"],
            }
            for item in registry["strategies"]
        ],
        "relevant_experience": relevant,
        "router_experience": [
            {
                "experience_id": item["experience_id"],
                "maturity": item["maturity"],
                "observation": item["observation"],
                "evidence_ref": item["evidence"]["evidence_ref"],
            }
            for item in registry["router_experience"]
        ],
        "decision_policy": registry["decision_policy"],
        "decision_contract": {
            "allowed_decisions": registry["decision_policy"]["decisions"],
            "allowed_strategies": [
                item["strategy_id"] for item in registry["strategies"]
            ],
            "evidence_required_for_dispatch": True,
            "no_relevant_experience": "request_qualification",
        },
        "provenance": {
            "router_policy_sha256": _sha256(policy_path),
            "experience_registry_sha256": _sha256(registry_path),
        },
    }
    serialized = json.dumps(context, sort_keys=True).lower()
    if any(term in serialized for term in LEGACY_ROUTER_TERMS):
        raise RouterExperienceError("Router context leaks a historical codename")
    return context


def build_prompt(*, policy_text: str, context: dict[str, Any]) -> str:
    """Compose the explicit, hashable Router request."""
    task_id = context["task"]["task_id"]
    return (
        policy_text.rstrip()
        + "\n\n--- Current evidence view ---\n\n"
        + json.dumps(context, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n\n--- Required response ---\n\n"
        + "Return exactly one JSON object and no surrounding text:\n\n"
        + json.dumps(
            {
                "schema": "modus-router-decision-v1",
                "task_id": task_id,
                "decision": "dispatch|abstain|request_qualification",
                "strategy": "one allowed strategy or null",
                "evidence_refs": ["required for dispatch"],
                "reason": "short evidence-grounded reason",
            },
            separators=(",", ":"),
        )
        + "\n"
    )


def build_batch_context(contexts: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine task contexts without duplicating policy or strategy authority."""
    if not isinstance(contexts, list) or not contexts:
        raise RouterExperienceError("batch contexts must be a non-empty list")
    first = contexts[0]
    task_ids = [context["task"]["task_id"] for context in contexts]
    if len(set(task_ids)) != len(task_ids):
        raise RouterExperienceError("batch task IDs must be unique")
    shared_fields = (
        "strategies", "router_experience", "decision_policy",
        "decision_contract", "provenance",
    )
    if any(
        context.get("schema") != CONTEXT_SCHEMA
        or any(context[field] != first[field] for field in shared_fields)
        for context in contexts
    ):
        raise RouterExperienceError("batch contexts do not share one policy view")
    batch = {
        "schema": BATCH_CONTEXT_SCHEMA,
        "tasks": [
            {
                "task": context["task"],
                "relevant_experience": context["relevant_experience"],
            }
            for context in contexts
        ],
        **{field: first[field] for field in shared_fields},
    }
    serialized = json.dumps(batch, sort_keys=True).lower()
    if any(term in serialized for term in LEGACY_ROUTER_TERMS):
        raise RouterExperienceError("Router batch context leaks a historical codename")
    return batch


def build_batch_prompt(*, policy_text: str, context: dict[str, Any]) -> str:
    """Compose one batched Router request over several formal task descriptors."""
    task_ids = [row["task"]["task_id"] for row in context["tasks"]]
    return (
        policy_text.rstrip()
        + "\n\n--- Current evidence view ---\n\n"
        + json.dumps(context, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n\n--- Required response ---\n\n"
        + "Return exactly one JSON object and no surrounding text. Return one "
        + "route for every task in the given order:\n\n"
        + json.dumps(
            {
                "schema": "modus-router-batch-decision-v1",
                "routes": [
                    {
                        "task_id": task_id,
                        "decision": "dispatch|abstain|request_qualification",
                        "strategy": "one allowed strategy or null",
                        "evidence_refs": ["required for dispatch"],
                        "reason": "short evidence-grounded reason",
                    }
                    for task_id in task_ids
                ],
            },
            separators=(",", ":"),
        )
        + "\n"
    )

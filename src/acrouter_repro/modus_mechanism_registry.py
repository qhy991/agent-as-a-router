"""Fail-closed loading and zero-token matching for Modus mechanism evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REGISTRY_SCHEMA = "acrouter-modus-mechanism-evidence-v1"
DESCRIPTOR_FIELDS = {
    "worker_model",
    "semantic_kind",
    "reuse_batches",
    "performance_objective",
}
MECHANISM_FIELDS = {
    "mechanism_id",
    "evidence_ref",
    "verified_profile",
    "router_eligible",
    "agent_router_eligible",
    "typed_matcher_eligible",
    "verification_status",
    "semantic_predicate",
    "applicability",
    "evidence",
}


class MechanismRegistryError(ValueError):
    """The registry or a typed task descriptor violates its frozen contract."""


def _nonempty_text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise MechanismRegistryError(f"{where} must be non-empty text")
    return value


def load_mechanism_registry(path: Path) -> dict[str, Any]:
    """Load a registry and verify every referenced evidence artifact hash."""
    path = path.expanduser().resolve()
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MechanismRegistryError("mechanism registry is unreadable") from error
    if not isinstance(registry, dict) or registry.get("schema") != REGISTRY_SCHEMA:
        raise MechanismRegistryError("mechanism registry schema differs")
    worker_model = _nonempty_text(registry.get("worker_model"), "worker_model")
    mechanisms = registry.get("mechanisms")
    if not isinstance(mechanisms, list) or not mechanisms:
        raise MechanismRegistryError("mechanisms must be a non-empty list")
    repository = path.parent.parent
    ids: set[str] = set()
    references: set[str] = set()
    for index, mechanism in enumerate(mechanisms):
        where = f"mechanisms[{index}]"
        if not isinstance(mechanism, dict) or set(mechanism) != MECHANISM_FIELDS:
            raise MechanismRegistryError(f"{where} fields differ")
        mechanism_id = _nonempty_text(
            mechanism["mechanism_id"], f"{where}.mechanism_id"
        )
        evidence_ref = _nonempty_text(
            mechanism["evidence_ref"], f"{where}.evidence_ref"
        )
        if mechanism_id in ids or evidence_ref in references:
            raise MechanismRegistryError("mechanism IDs and evidence refs must be unique")
        ids.add(mechanism_id)
        references.add(evidence_ref)
        _nonempty_text(mechanism["verified_profile"], f"{where}.verified_profile")
        _nonempty_text(
            mechanism["verification_status"], f"{where}.verification_status"
        )
        for flag in (
            "router_eligible",
            "agent_router_eligible",
            "typed_matcher_eligible",
        ):
            if not isinstance(mechanism[flag], bool):
                raise MechanismRegistryError(f"{where}.{flag} must be boolean")
        semantic = mechanism["semantic_predicate"]
        if not isinstance(semantic, dict) or set(semantic) != {"kind", "description"}:
            raise MechanismRegistryError(f"{where}.semantic_predicate fields differ")
        _nonempty_text(semantic["kind"], f"{where}.semantic_predicate.kind")
        _nonempty_text(
            semantic["description"], f"{where}.semantic_predicate.description"
        )
        applicability = mechanism["applicability"]
        expected_applicability = {
            "minimum_reuse_batches",
            "setup_operation",
            "performance_objective",
        }
        if (
            not isinstance(applicability, dict)
            or set(applicability) != expected_applicability
        ):
            raise MechanismRegistryError(f"{where}.applicability fields differ")
        reuse = applicability["minimum_reuse_batches"]
        if not isinstance(reuse, int) or isinstance(reuse, bool) or reuse < 1:
            raise MechanismRegistryError(
                f"{where}.applicability.minimum_reuse_batches is invalid"
            )
        _nonempty_text(
            applicability["setup_operation"],
            f"{where}.applicability.setup_operation",
        )
        _nonempty_text(
            applicability["performance_objective"],
            f"{where}.applicability.performance_objective",
        )
        evidence = mechanism["evidence"]
        if not isinstance(evidence, list) or not evidence:
            raise MechanismRegistryError(f"{where}.evidence must be non-empty")
        for evidence_index, item in enumerate(evidence):
            evidence_where = f"{where}.evidence[{evidence_index}]"
            if not isinstance(item, dict) or set(item) != {"kind", "path", "sha256"}:
                raise MechanismRegistryError(f"{evidence_where} fields differ")
            _nonempty_text(item["kind"], f"{evidence_where}.kind")
            relative = Path(_nonempty_text(item["path"], f"{evidence_where}.path"))
            if relative.is_absolute() or ".." in relative.parts:
                raise MechanismRegistryError(f"{evidence_where}.path is not repository-relative")
            digest = _nonempty_text(item["sha256"], f"{evidence_where}.sha256")
            artifact = repository / relative
            if not artifact.is_file():
                raise MechanismRegistryError(f"{evidence_where}.path is missing")
            if hashlib.sha256(artifact.read_bytes()).hexdigest() != digest:
                raise MechanismRegistryError(f"{evidence_where}.sha256 differs")
    registry["worker_model"] = worker_model
    return registry


def match_typed_mechanisms(
    registry: dict[str, Any],
    descriptor: dict[str, Any],
) -> list[dict[str, str]]:
    """Return only exactly compatible, typed-matcher-eligible mechanisms."""
    if not isinstance(descriptor, dict) or set(descriptor) != DESCRIPTOR_FIELDS:
        raise MechanismRegistryError("typed task descriptor fields differ")
    worker_model = _nonempty_text(descriptor["worker_model"], "worker_model")
    semantic_kind = _nonempty_text(descriptor["semantic_kind"], "semantic_kind")
    objective = _nonempty_text(
        descriptor["performance_objective"], "performance_objective"
    )
    reuse = descriptor["reuse_batches"]
    if not isinstance(reuse, int) or isinstance(reuse, bool) or reuse < 1:
        raise MechanismRegistryError("reuse_batches must be a positive integer")
    if worker_model != registry["worker_model"]:
        return []
    matches = []
    for mechanism in registry["mechanisms"]:
        applicability = mechanism["applicability"]
        if not mechanism["typed_matcher_eligible"]:
            continue
        if mechanism["semantic_predicate"]["kind"] != semantic_kind:
            continue
        if applicability["performance_objective"] != objective:
            continue
        if reuse < applicability["minimum_reuse_batches"]:
            continue
        matches.append({
            "mechanism_id": mechanism["mechanism_id"],
            "profile": mechanism["verified_profile"],
            "evidence_ref": mechanism["evidence_ref"],
        })
    return matches


def resolve_typed_candidates(
    candidates: list[dict[str, str]],
) -> dict[str, Any]:
    """Resolve candidate cardinality without inventing a neutral fallback."""
    if not isinstance(candidates, list) or not all(
        isinstance(candidate, dict)
        and set(candidate) == {"mechanism_id", "profile", "evidence_ref"}
        and all(isinstance(value, str) and value for value in candidate.values())
        for candidate in candidates
    ):
        raise MechanismRegistryError("typed candidates are invalid")
    if not candidates:
        return {
            "decision": "defer",
            "reason": "unqualified_task_state",
            "candidates": [],
        }
    if len(candidates) == 1:
        return {
            "decision": "dispatch",
            "reason": "single_typed_candidate",
            "action": candidates[0],
        }
    return {
        "decision": "compare",
        "reason": "multiple_typed_candidates",
        "candidates": candidates,
    }

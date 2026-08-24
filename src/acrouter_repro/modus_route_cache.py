"""Exact, evidence-bound cache for previously verified Modus Agent routes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


KEY_SCHEMA = "modus-route-cache-key-v1"
ENTRY_SCHEMA = "modus-route-cache-entry-v1"
KEY_FIELDS = {
    "schema", "task_contract_sha256", "typed_descriptor_sha256",
    "router_prompt_sha256", "model", "allowed_actions", "profile_digests",
}
ENTRY_FIELDS = {
    "schema", "key", "key_sha256", "decision", "decision_sha256", "evidence",
}
EVIDENCE_FIELDS = {
    "router_score_path", "router_score_sha256", "router_usage_tokens",
}


class RouteCacheMiss(ValueError):
    """The current exact routing identity has no usable cached decision."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _digest(value: Any, where: str) -> str:
    if (
        not isinstance(value, str) or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{where} must be a lowercase sha256")
    return value


def validate_key(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != KEY_FIELDS:
        raise ValueError("route cache key fields differ")
    if value["schema"] != KEY_SCHEMA:
        raise ValueError("route cache key schema differs")
    for field in (
        "task_contract_sha256", "typed_descriptor_sha256", "router_prompt_sha256",
    ):
        _digest(value[field], f"key.{field}")
    model = value["model"]
    if (
        not isinstance(model, dict) or set(model) != {"slug", "reasoning_effort"}
        or not all(isinstance(item, str) and item for item in model.values())
    ):
        raise ValueError("key.model is invalid")
    actions = value["allowed_actions"]
    if (
        not isinstance(actions, list) or not actions
        or not all(isinstance(action, str) and action for action in actions)
        or len(set(actions)) != len(actions)
    ):
        raise ValueError("key.allowed_actions is invalid")
    profiles = value["profile_digests"]
    if not isinstance(profiles, dict) or set(profiles) != set(actions):
        raise ValueError("key.profile_digests must exactly match allowed actions")
    for action, digest in profiles.items():
        _digest(digest, f"key.profile_digests.{action}")
    return value


def build_key(
    *, task_contract_sha256: str, typed_descriptor: Any,
    router_prompt_sha256: str, model_slug: str, reasoning_effort: str,
    allowed_actions: list[str], profile_digests: dict[str, str],
) -> dict[str, Any]:
    return validate_key({
        "schema": KEY_SCHEMA,
        "task_contract_sha256": task_contract_sha256,
        "typed_descriptor_sha256": sha256_value(typed_descriptor),
        "router_prompt_sha256": router_prompt_sha256,
        "model": {"slug": model_slug, "reasoning_effort": reasoning_effort},
        "allowed_actions": allowed_actions,
        "profile_digests": profile_digests,
    })


def _validate_decision(decision: Any, key: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(decision, dict) or set(decision) != {"actions_by_stage"}:
        raise ValueError("cached decision fields differ")
    routes = decision["actions_by_stage"]
    if not isinstance(routes, dict) or not routes:
        raise ValueError("cached actions_by_stage is invalid")
    allowed = set(key["allowed_actions"])
    if not all(
        isinstance(stage, str) and stage
        and isinstance(action, str) and action in allowed
        for stage, action in routes.items()
    ):
        raise ValueError("cached decision contains an unsupported route")
    return decision


def build_entry(
    *, key: dict[str, Any], decision: dict[str, Any],
    router_score_path: str, router_score_sha256: str, router_usage_tokens: int,
) -> dict[str, Any]:
    key = validate_key(key)
    decision = _validate_decision(decision, key)
    if not isinstance(router_score_path, str) or not router_score_path:
        raise ValueError("router_score_path is invalid")
    _digest(router_score_sha256, "router_score_sha256")
    if (
        not isinstance(router_usage_tokens, int) or isinstance(router_usage_tokens, bool)
        or router_usage_tokens <= 0
    ):
        raise ValueError("router_usage_tokens must be a positive integer")
    return {
        "schema": ENTRY_SCHEMA,
        "key": key,
        "key_sha256": sha256_value(key),
        "decision": decision,
        "decision_sha256": sha256_value(decision),
        "evidence": {
            "router_score_path": router_score_path,
            "router_score_sha256": router_score_sha256,
            "router_usage_tokens": router_usage_tokens,
        },
    }


def load_cached_route(
    entry_path: Path, *, current_key: dict[str, Any], evidence_root: Path,
) -> dict[str, Any]:
    try:
        value = json.loads(entry_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RouteCacheMiss("route cache entry is unreadable") from error
    try:
        if not isinstance(value, dict) or set(value) != ENTRY_FIELDS:
            raise ValueError("entry fields differ")
        if value["schema"] != ENTRY_SCHEMA:
            raise ValueError("entry schema differs")
        cached_key = validate_key(value["key"])
        current_key = validate_key(current_key)
        if value["key_sha256"] != sha256_value(cached_key):
            raise ValueError("cached key digest differs")
        if sha256_value(current_key) != value["key_sha256"]:
            raise ValueError("current routing identity differs")
        decision = _validate_decision(value["decision"], current_key)
        if value["decision_sha256"] != sha256_value(decision):
            raise ValueError("cached decision digest differs")
        evidence = value["evidence"]
        if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_FIELDS:
            raise ValueError("cached evidence fields differ")
        _digest(evidence["router_score_sha256"], "evidence.router_score_sha256")
        if not isinstance(evidence["router_usage_tokens"], int) or evidence["router_usage_tokens"] <= 0:
            raise ValueError("cached evidence usage is invalid")
        evidence_path = evidence_root / evidence["router_score_path"]
        if not evidence_path.is_file():
            raise ValueError("cached evidence file is missing")
        if hashlib.sha256(evidence_path.read_bytes()).hexdigest() != evidence["router_score_sha256"]:
            raise ValueError("cached evidence file digest differs")
    except ValueError as error:
        raise RouteCacheMiss(str(error)) from error
    return {
        "actions_by_stage": dict(decision["actions_by_stage"]),
        "from_cache": True,
        "router_model_calls": 0,
        "router_tokens": 0,
        "source_entry_sha256": hashlib.sha256(entry_path.read_bytes()).hexdigest(),
    }

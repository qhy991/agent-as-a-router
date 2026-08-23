import hashlib
import json
from pathlib import Path
import unittest

from acrouter_repro.modus_mechanism_registry import (
    MechanismRegistryError,
    load_mechanism_registry,
    match_typed_mechanisms,
    resolve_typed_candidates,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs/modus_mechanism_evidence.json"


class ModusMechanismEvidenceTest(unittest.TestCase):
    def test_registry_has_unique_bound_mechanisms_and_live_evidence(self):
        registry = json.loads(REGISTRY.read_text())
        self.assertEqual(registry["schema"], "acrouter-modus-mechanism-evidence-v1")
        self.assertEqual(registry["worker_model"], "gpt-5.6-luna")
        mechanisms = registry["mechanisms"]
        self.assertEqual(
            [row["mechanism_id"] for row in mechanisms],
            ["shared-ordered-search-v1", "shared-prefix-sum-v1"],
        )
        self.assertEqual(
            len({row["evidence_ref"] for row in mechanisms}),
            len(mechanisms),
        )
        for mechanism in mechanisms:
            self.assertIn(mechanism["verified_profile"], {"neutral", "p000", "p100"})
            self.assertIsInstance(mechanism["router_eligible"], bool)
            self.assertGreaterEqual(
                mechanism["applicability"]["minimum_reuse_batches"],
                1,
            )
            self.assertTrue(mechanism["semantic_predicate"]["kind"])
            self.assertTrue(mechanism["evidence"])
            for evidence in mechanism["evidence"]:
                path = ROOT / evidence["path"]
                self.assertTrue(path.is_file(), evidence["path"])
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    evidence["sha256"],
                    evidence["path"],
                )

    def test_failed_outcome_blind_matching_revokes_router_eligibility(self):
        registry = json.loads(REGISTRY.read_text())
        eligible = [
            row["mechanism_id"]
            for row in registry["mechanisms"]
            if row["router_eligible"]
        ]
        self.assertEqual(eligible, [])

    def test_typed_matcher_filters_model_kind_objective_and_reuse(self):
        registry = load_mechanism_registry(REGISTRY)
        base = {
            "worker_model": "gpt-5.6-luna",
            "semantic_kind": "ordered_search",
            "reuse_batches": 20,
            "performance_objective": "latency_subject_to_correctness_then_tokens",
        }
        self.assertEqual(
            match_typed_mechanisms(registry, base),
            [{
                "mechanism_id": "shared-ordered-search-v1",
                "profile": "p100",
                "evidence_ref": "case:rankcount-prefixcount-n3",
            }],
        )
        for change in (
            {"worker_model": "gpt-5.6-sol"},
            {"semantic_kind": "token_frequency"},
            {"reuse_batches": 1},
            {"performance_objective": "minimize_tokens_only"},
        ):
            with self.subTest(change=change):
                descriptor = {**base, **change}
                self.assertEqual(match_typed_mechanisms(registry, descriptor), [])

    def test_typed_matcher_replays_trusted_task_descriptors(self):
        registry = load_mechanism_registry(REGISTRY)
        cases = {
            "nearest-p01": ("ordered_search", 1, []),
            "nearest-p02": (
                "ordered_search",
                20,
                ["shared-ordered-search-v1"],
            ),
            "frequency-p02": ("token_frequency", 20, []),
            "lookup-p02": ("canonical_key_lookup", 20, []),
            "interval-p02": ("interval_membership", 20, []),
        }
        for task, (kind, reuse, expected) in cases.items():
            with self.subTest(task=task):
                matches = match_typed_mechanisms(registry, {
                    "worker_model": "gpt-5.6-luna",
                    "semantic_kind": kind,
                    "reuse_batches": reuse,
                    "performance_objective": (
                        "latency_subject_to_correctness_then_tokens"
                    ),
                })
                self.assertEqual(
                    [row["mechanism_id"] for row in matches],
                    expected,
                )

    def test_registry_and_descriptor_fail_closed(self):
        registry = load_mechanism_registry(REGISTRY)
        with self.assertRaises(MechanismRegistryError):
            match_typed_mechanisms(registry, {
                "worker_model": "gpt-5.6-luna",
                "semantic_kind": "ordered_search",
                "reuse_batches": 0,
                "performance_objective": (
                    "latency_subject_to_correctness_then_tokens"
                ),
            })

    def test_candidate_cardinality_resolves_to_defer_dispatch_or_compare(self):
        candidate = {
            "mechanism_id": "shared-ordered-search-v1",
            "profile": "p100",
            "evidence_ref": "case:rankcount-prefixcount-n3",
        }
        self.assertEqual(resolve_typed_candidates([]), {
            "decision": "defer",
            "reason": "unqualified_task_state",
            "candidates": [],
        })
        self.assertEqual(resolve_typed_candidates([candidate]), {
            "decision": "dispatch",
            "reason": "single_typed_candidate",
            "action": candidate,
        })
        second = {
            "mechanism_id": "another-mechanism",
            "profile": "p000",
            "evidence_ref": "case:another",
        }
        self.assertEqual(resolve_typed_candidates([candidate, second]), {
            "decision": "compare",
            "reason": "multiple_typed_candidates",
            "candidates": [candidate, second],
        })


if __name__ == "__main__":
    unittest.main()

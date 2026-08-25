import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from acrouter_repro.modus_router_experience import (
    RouterExperienceError,
    build_batch_context,
    build_batch_prompt,
    build_context,
    load_descriptor,
    load_registry,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "router/AGENTS.md"
REGISTRY = ROOT / "configs/modus_profile_experience_registry.json"
BASE = ROOT / "examples/modus_profile_router/profile-experience-transfer"
FORMAL_STRATEGIES = {
    "unconstrained-optimization",
    "target-scoped-optimization",
    "prepared-shared-optimization",
}
LEGACY_TERMS = ("p2s", "p2t", "p000", "p100", "e1v2", "e1v3")


class ModusRouterExperienceTest(unittest.TestCase):
    def setUp(self):
        self.registry = load_registry(REGISTRY)

    def test_policy_and_router_projection_use_only_formal_names(self):
        policy = POLICY.read_text().lower()
        self.assertFalse(any(term in policy for term in LEGACY_TERMS))
        text = (BASE / "router-context.json").read_text().lower()
        self.assertFalse(any(term in text for term in LEGACY_TERMS))
        value = json.loads(text)
        self.assertEqual(
            {row["strategy_id"] for row in value["strategies"]},
            FORMAL_STRATEGIES,
        )

    def test_each_transfer_descriptor_gets_one_relevant_experience(self):
        expected = {
            "single-batch-keyed-reduction": "target-scoped-optimization",
            "repeated-batch-keyed-aggregate": "prepared-shared-optimization",
            "direct-bit-transformation": "target-scoped-optimization",
        }
        for task_id, strategy in expected.items():
            with self.subTest(task=task_id):
                descriptor = load_descriptor(BASE / f"task-descriptors/{task_id}.json")
                context = build_context(
                    registry=self.registry,
                    descriptor=descriptor,
                    policy_path=POLICY,
                    registry_path=REGISTRY,
                )
                self.assertEqual(len(context["relevant_experience"]), 1)
                self.assertEqual(
                    context["relevant_experience"][0]["selected_strategy"], strategy
                )
                self.assertTrue(
                    context["relevant_experience"][0]["evidence_ref"].startswith(
                        "evidence:profile-affinity:"
                    )
                )

    def test_repeated_work_exposes_performance_rejection(self):
        context = json.loads((BASE / "router-context.json").read_text())
        repeated = next(
            row for row in context["tasks"]
            if row["task"]["task_id"] == "repeated-batch-keyed-aggregate"
        )
        rejected = repeated["relevant_experience"][0]["rejected_strategies"]
        self.assertEqual(rejected[0]["strategy_id"], "target-scoped-optimization")
        self.assertEqual(rejected[0]["reason"], "performance-ineligible")
        self.assertGreater(rejected[0]["performance_ratio_to_unconstrained"], 8.0)

    def test_unknown_signature_has_no_relevant_experience(self):
        descriptor = load_descriptor(
            BASE / "task-descriptors/single-batch-keyed-reduction.json"
        )
        descriptor["semantic_kind"] = "unknown-semantic-kind"
        context = build_context(
            registry=self.registry,
            descriptor=descriptor,
            policy_path=POLICY,
            registry_path=REGISTRY,
        )
        self.assertEqual(context["relevant_experience"], [])
        self.assertEqual(
            context["decision_contract"]["no_relevant_experience"],
            "request_qualification",
        )

    def test_registry_is_hash_bound_and_tamper_fails(self):
        raw = json.loads(REGISTRY.read_text())
        raw["task_experience"][0]["evidence"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "configs" / "registry.json"
            path.parent.mkdir()
            path.write_text(json.dumps(raw))
            with self.assertRaisesRegex(
                RouterExperienceError, "artifact is missing or changed"
            ):
                load_registry(path)

    def test_policy_and_registry_hashes_are_in_context(self):
        value = json.loads(
            (BASE / "router-context.json").read_text()
        )
        self.assertEqual(
            value["provenance"]["router_policy_sha256"],
            hashlib.sha256(POLICY.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            value["provenance"]["experience_registry_sha256"],
            hashlib.sha256(REGISTRY.read_bytes()).hexdigest(),
        )

    def test_batch_prompt_uses_one_policy_and_formal_task_order(self):
        contexts = []
        for task_id in (
            "single-batch-keyed-reduction",
            "repeated-batch-keyed-aggregate",
            "direct-bit-transformation",
        ):
            contexts.append(build_context(
                registry=self.registry,
                descriptor=load_descriptor(BASE / f"task-descriptors/{task_id}.json"),
                policy_path=POLICY,
                registry_path=REGISTRY,
            ))
        batch = build_batch_context(contexts)
        self.assertEqual(
            batch,
            json.loads((BASE / "router-context.json").read_text()),
        )
        prompt = build_batch_prompt(policy_text=POLICY.read_text(), context=batch)
        self.assertEqual(prompt, (BASE / "router-task.md").read_text())
        self.assertEqual(prompt.count("# Modus Profile Router"), 1)
        self.assertLess(
            prompt.index("single-batch-keyed-reduction"),
            prompt.index("repeated-batch-keyed-aggregate"),
        )
        self.assertLess(
            prompt.index("repeated-batch-keyed-aggregate"),
            prompt.index("direct-bit-transformation"),
        )


if __name__ == "__main__":
    unittest.main()

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from acrouter_repro.modus_route_cache import (
    RouteCacheMiss,
    build_entry,
    build_key,
    load_cached_route,
)


EMPTY = hashlib.sha256(b"").hexdigest()
ROOT = Path(__file__).resolve().parents[1]


class ModusRouteCacheTest(unittest.TestCase):
    def key(self):
        return build_key(
            task_contract_sha256="1" * 64,
            typed_descriptor={"stages": [{"id": "L", "batches": 1}, {"id": "S", "batches": 120}]},
            router_prompt_sha256="2" * 64,
            model_slug="gpt-5.6-luna",
            reasoning_effort="max",
            allowed_actions=["neutral", "p000", "e1v2"],
            profile_digests={"neutral": EMPTY, "p000": "3" * 64, "e1v2": "4" * 64},
        )

    def fixture(self, root: Path):
        evidence = root / "evidence/router-score.json"
        evidence.parent.mkdir()
        evidence.write_text('{"status":"pass"}\n')
        entry = build_entry(
            key=self.key(),
            decision={"actions_by_stage": {"stage-L": "p000", "stage-S": "e1v2"}},
            router_score_path="evidence/router-score.json",
            router_score_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
            router_usage_tokens=15951,
        )
        path = root / "route-cache.json"
        path.write_text(json.dumps(entry, indent=2) + "\n")
        return path, evidence

    def test_exact_hit_is_zero_model_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry, _ = self.fixture(root)
            result = load_cached_route(entry, current_key=self.key(), evidence_root=root)
            self.assertEqual(result["actions_by_stage"], {"stage-L": "p000", "stage-S": "e1v2"})
            self.assertTrue(result["from_cache"])
            self.assertEqual(result["router_model_calls"], 0)
            self.assertEqual(result["router_tokens"], 0)

    def test_every_routing_identity_change_misses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry, _ = self.fixture(root)
            mutations = [
                ("task_contract_sha256", "5" * 64),
                ("typed_descriptor_sha256", "5" * 64),
                ("router_prompt_sha256", "5" * 64),
            ]
            for field, value in mutations:
                key = copy.deepcopy(self.key())
                key[field] = value
                with self.subTest(field=field), self.assertRaises(RouteCacheMiss):
                    load_cached_route(entry, current_key=key, evidence_root=root)
            for field, value in (("slug", "other-model"), ("reasoning_effort", "high")):
                key = copy.deepcopy(self.key())
                key["model"][field] = value
                with self.subTest(model_field=field), self.assertRaises(RouteCacheMiss):
                    load_cached_route(entry, current_key=key, evidence_root=root)
            key = copy.deepcopy(self.key())
            key["allowed_actions"] = ["neutral", "p000"]
            key["profile_digests"].pop("e1v2")
            with self.assertRaises(RouteCacheMiss):
                load_cached_route(entry, current_key=key, evidence_root=root)
            key = copy.deepcopy(self.key())
            key["profile_digests"]["p000"] = "5" * 64
            with self.assertRaises(RouteCacheMiss):
                load_cached_route(entry, current_key=key, evidence_root=root)

    def test_missing_or_tampered_evidence_and_decision_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry, evidence = self.fixture(root)
            evidence.unlink()
            with self.assertRaises(RouteCacheMiss):
                load_cached_route(entry, current_key=self.key(), evidence_root=root)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry, evidence = self.fixture(root)
            evidence.write_text("tampered\n")
            with self.assertRaises(RouteCacheMiss):
                load_cached_route(entry, current_key=self.key(), evidence_root=root)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry, _ = self.fixture(root)
            value = json.loads(entry.read_text())
            value["decision"]["actions_by_stage"]["stage-S"] = "neutral"
            entry.write_text(json.dumps(value))
            with self.assertRaises(RouteCacheMiss):
                load_cached_route(entry, current_key=self.key(), evidence_root=root)

    def test_p2c_real_router_decision_replays_without_model(self):
        config = json.loads((ROOT / "configs/modus_p2c_route_cache_v1.json").read_text())
        key = build_key(
            task_contract_sha256=config["task_contract_sha256"],
            typed_descriptor=config["typed_descriptor"],
            router_prompt_sha256=config["router_prompt_sha256"],
            model_slug=config["model"]["slug"],
            reasoning_effort=config["model"]["reasoning_effort"],
            allowed_actions=config["allowed_actions"],
            profile_digests=config["profile_digests"],
        )
        entry = ROOT / "examples/modus_profile_router/long-horizon-p2c-v1/route-cache.json"
        result = load_cached_route(entry, current_key=key, evidence_root=ROOT)
        self.assertEqual(result["actions_by_stage"], {"stage-L": "p000", "stage-S": "e1v2"})
        self.assertEqual(result["router_model_calls"], 0)
        self.assertEqual(result["router_tokens"], 0)
        drifted = copy.deepcopy(key)
        drifted["router_prompt_sha256"] = "f" * 64
        with self.assertRaises(RouteCacheMiss):
            load_cached_route(entry, current_key=drifted, evidence_root=ROOT)

    def test_mechanism_evidence_keeps_cached_economics_post_outcome(self):
        path = ROOT / "agentic-artifacts/modus-route-cache-p2c-mechanism-v1.json"
        value = json.loads(path.read_text())
        self.assertFalse(value["scientific_evidence"])
        self.assertTrue(value["model_free_mechanism_evidence"])
        self.assertEqual(value["verification"]["exact_hit_router_model_calls"], 0)
        self.assertEqual(value["verification"]["exact_hit_router_tokens"], 0)
        self.assertEqual(value["p2c_cached_route_counterfactual"]["break_even_deployments"], 8)
        self.assertEqual(value["p2c_cached_route_counterfactual"]["net_tokens_at_expected_deployments"], 9371)
        self.assertFalse(value["decision"]["prospective_economic_claim_ready"])
        for file_key, hash_key in (
            ("owner", "owner_sha256"),
            ("builder", "builder_sha256"),
            ("entry", "entry_sha256"),
        ):
            self.assertEqual(
                hashlib.sha256((ROOT / value["files"][file_key]).read_bytes()).hexdigest(),
                value["files"][hash_key],
            )


if __name__ == "__main__":
    unittest.main()

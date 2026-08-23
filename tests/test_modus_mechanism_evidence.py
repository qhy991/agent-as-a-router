import hashlib
import json
from pathlib import Path
import unittest


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

    def test_only_fully_qualified_mechanism_is_router_eligible(self):
        registry = json.loads(REGISTRY.read_text())
        eligible = [
            row["mechanism_id"]
            for row in registry["mechanisms"]
            if row["router_eligible"]
        ]
        self.assertEqual(eligible, ["shared-ordered-search-v1"])


if __name__ == "__main__":
    unittest.main()

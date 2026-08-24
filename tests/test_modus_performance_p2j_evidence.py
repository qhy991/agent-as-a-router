import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-performance-p2j-positive-v1.json"


class ModusPerformanceP2jEvidenceTest(unittest.TestCase):
    def test_t_only_candidate_is_jointly_eligible(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertEqual(value["formal_status"], "valid_positive")
        self.assertTrue(value["prospective_profile_revision_evidence"])
        self.assertEqual(value["profile_revision"]["changed_axis"], "T only")
        self.assertTrue(value["gates"]["p000v2_performance"])
        self.assertTrue(value["gates"]["p000v2_token_saving"])
        self.assertTrue(value["gates"]["p000v2_noise"])
        self.assertTrue(value["gates"]["p000v2_eligible"])
        self.assertFalse(value["gates"]["p000_eligible"])

    def test_promotion_is_bounded_to_p2k(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertEqual(value["decision"]["frozen_scorer"], "promote_p000v2_to_p2k")
        self.assertTrue(value["decision"]["p2k_use_authorized"])
        self.assertFalse(value["decision"]["global_replacement_of_p000_authorized"])
        self.assertFalse(value["decision"]["second_triplet_authorized"])
        self.assertGreater(value["common_metrics"]["net_tokens_at_8_deployments"], 0)

    def test_every_named_evidence_file_is_hash_bound(self):
        value = json.loads(EVIDENCE.read_text())
        files = value["files"]
        for key, path in files.items():
            if key.endswith("_sha256"):
                continue
            expected = files[key + "_sha256"]
            actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, key)


if __name__ == "__main__":
    unittest.main()

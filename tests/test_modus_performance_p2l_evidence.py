import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-performance-p2l-final-v1.json"


class ModusPerformanceP2lEvidenceTest(unittest.TestCase):
    def test_representation_revision_improves_reliability_but_is_rejected(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertEqual(value["formal_status"], "valid_rejection")
        self.assertEqual(value["per_repetition"]["e1v3_representation_semantics_passed"], "2/2")
        self.assertEqual(value["per_repetition"]["e1v2_representation_semantics_passed"], "1/2")
        self.assertTrue(value["gates"]["e1v3_two_valid_repetitions"])
        self.assertTrue(value["gates"]["e1v3_median_performance"])
        self.assertFalse(value["gates"]["e1v3_per_repetition_performance"])
        self.assertTrue(value["gates"]["e1v3_token_saving"])
        self.assertFalse(value["gates"]["e1v3_eligible"])

    def test_no_p2m_or_qualified_economics(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertFalse(value["decision"]["p2m_authorized"])
        self.assertFalse(value["decision"]["third_triplet_authorized"])
        self.assertIsNone(value["economics"]["qualified_break_even_deployments"])
        self.assertIsNone(value["economics"]["qualified_net_tokens_at_8_deployments"])

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

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-long-horizon-p2i-negative-v1.json"


class LongHorizonP2iNegativeEvidenceTest(unittest.TestCase):
    def test_valid_pair_is_rejected_only_by_stage_l_performance(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertEqual(value["formal_status"], "valid_negative")
        self.assertTrue(value["prospective_observable_contract_negative_evidence"])
        self.assertTrue(value["gates"]["both_pipelines_valid"])
        self.assertFalse(value["gates"]["stage_l_performance"])
        self.assertTrue(value["gates"]["final_performance"])
        self.assertTrue(value["gates"]["worker_token_saving"])
        self.assertTrue(value["gates"]["noise"])
        self.assertFalse(value["gates"]["route_qualified"])

    def test_failed_performance_gate_blocks_raw_positive_economics(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertGreater(value["common_metrics"]["worker_token_saving_fraction"], 0.40)
        self.assertGreater(value["common_metrics"]["stage_l_proposed_ratio_to_fastest"], 1.25)
        self.assertFalse(value["decision"]["deployment_authorized"])
        self.assertFalse(value["decision"]["second_pair_authorized"])
        self.assertEqual(value["decision"]["frozen_scorer"], "stop_negative")

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

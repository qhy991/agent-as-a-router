import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-long-horizon-p2k-final-v1.json"


class LongHorizonP2kEvidenceTest(unittest.TestCase):
    def test_correct_composed_route_is_rejected_by_performance_and_noise(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertEqual(value["formal_status"], "valid_rejection")
        self.assertEqual(value["validity"]["complete_pipelines"], 4)
        self.assertTrue(value["validity"]["correctness_topology_and_mechanism_passed"])
        self.assertTrue(value["gates"]["worker_token_saving"])
        self.assertFalse(value["gates"]["median_final_performance"])
        self.assertFalse(value["gates"]["second_pair_noise_resolution"])
        self.assertFalse(value["gates"]["route_qualified"])

    def test_raw_positive_economics_cannot_authorize_deployment(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertGreater(value["replicated_aggregates"]["worker_saving_fraction"], 0.40)
        self.assertGreater(value["replicated_aggregates"]["proposed_final_ratio_to_fastest"], 1.25)
        self.assertIsNone(value["economics"]["qualified_break_even_deployments"])
        self.assertIsNone(value["economics"]["qualified_net_tokens_at_8_deployments"])
        self.assertFalse(value["decision"]["deployment_authorized"])
        self.assertFalse(value["decision"]["third_pair_authorized"])

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

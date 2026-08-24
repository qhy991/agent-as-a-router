import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_performance_p2n_agent_router_v1.json"


class ModusPerformanceP2nRouterTest(unittest.TestCase):
    def test_one_call_precedes_full_matrix(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["router"]["repetitions"], 1)
        self.assertFalse(value["router"]["worker_outcomes_available"])
        self.assertTrue(value["next_phase"]["full_nine_cell_matrix_authorized_after_valid_router"])
        self.assertFalse(value["next_phase"]["worker_deployment_authorized"])

    def test_profiles_evidence_and_scorer_are_hash_bound(self):
        value = json.loads(PROTOCOL.read_text())
        for row in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(row["profile_path"]).read_bytes()).hexdigest(), row["profile_sha256"])
        for row in value["prior_evidence"].values():
            self.assertEqual(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest(), row["sha256"])
        prompt = ROOT / value["router"]["prompt"]
        self.assertEqual(hashlib.sha256(prompt.read_bytes()).hexdigest(), value["router"]["prompt_sha256"])
        qualification = ROOT / value["tasks"]["qualification_path"]
        self.assertTrue(json.loads(qualification.read_text())["passed"])
        self.assertEqual(hashlib.sha256(qualification.read_bytes()).hexdigest(), value["tasks"]["qualification_sha256"])
        scorer = ROOT / value["provenance"]["scorer_path"]
        self.assertEqual(hashlib.sha256(scorer.read_bytes()).hexdigest(), value["provenance"]["scorer_sha256"])


if __name__ == "__main__":
    unittest.main()

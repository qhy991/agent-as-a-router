import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2b_agent_router_v1.json"


class LongHorizonP2bRouterTest(unittest.TestCase):
    def test_protocol_reuses_qualified_rule_with_one_call(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["router"]["repetitions"], 1)
        self.assertFalse(value["router"]["worker_outcomes_available"])
        self.assertFalse(value["pipeline_stage"]["authorized_before_router"])
        self.assertEqual(value["pipeline_stage"]["frozen_first_pair_order"], ["neutral", "routed"])
        self.assertEqual(value["expected_future_deployments"], 8)

    def test_inputs_profiles_prior_evidence_and_scorer_are_bound(self):
        value = json.loads(PROTOCOL.read_text())
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        for key in ("stage_l", "stage_s"):
            path = ROOT / value["task"][f"{key}_prompt"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["task"][f"{key}_prompt_sha256"])
        seed = ROOT / value["task"]["seed_root"]
        for relative, digest in value["task"]["seed_files_sha256"].items():
            self.assertEqual(hashlib.sha256((seed / relative).read_bytes()).hexdigest(), digest)
        qualification = ROOT / value["task"]["qualification_path"]
        self.assertEqual(hashlib.sha256(qualification.read_bytes()).hexdigest(), value["task"]["qualification_sha256"])
        prior = ROOT / value["prior_qualification"]["path"]
        self.assertEqual(hashlib.sha256(prior.read_bytes()).hexdigest(), value["prior_qualification"]["sha256"])
        scorer = ROOT / value["provenance"]["scorer_path"]
        self.assertEqual(hashlib.sha256(scorer.read_bytes()).hexdigest(), value["provenance"]["scorer_sha256_at_freeze"])


if __name__ == "__main__":
    unittest.main()

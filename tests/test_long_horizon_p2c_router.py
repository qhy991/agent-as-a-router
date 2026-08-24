import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2c_agent_router_v1.json"

class LongHorizonP2cRouterTest(unittest.TestCase):
    def test_frozen_one_call_transfer(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["router"]["repetitions"], 1)
        self.assertFalse(value["router"]["worker_outcomes_available"])
        self.assertEqual(value["pipeline_stage"]["frozen_first_pair_order"], ["routed", "neutral"])
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        for key in ("stage_l", "stage_s"):
            path = ROOT / value["task"][f"{key}_prompt"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["task"][f"{key}_prompt_sha256"])
        seed = ROOT / value["task"]["seed_root"]
        tree = hashlib.sha256()
        for path in sorted(seed.rglob("*")):
            if path.is_file():
                tree.update(str(path.relative_to(seed)).encode() + b"\0" + path.read_bytes() + b"\0")
        self.assertEqual(tree.hexdigest(), value["task"]["seed_tree_sha256"])
        qualification = ROOT / value["task"]["qualification_path"]
        self.assertEqual(hashlib.sha256(qualification.read_bytes()).hexdigest(), value["task"]["qualification_sha256"])
        prior = ROOT / value["prior_transfer"]["path"]
        self.assertEqual(hashlib.sha256(prior.read_bytes()).hexdigest(), value["prior_transfer"]["sha256"])
        scorer = ROOT / value["provenance"]["scorer_path"]
        self.assertEqual(hashlib.sha256(scorer.read_bytes()).hexdigest(), value["provenance"]["scorer_sha256"])

if __name__ == "__main__": unittest.main()

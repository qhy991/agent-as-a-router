import hashlib
import json
from pathlib import Path
import unittest

from scripts.score_modus_long_horizon_p2a_router import _parse_decision


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2a_agent_router_v1.json"


class LongHorizonP2aAgentRouterTest(unittest.TestCase):
    def load(self):
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_router_is_outcome_blind_and_precedes_pipeline(self):
        value = self.load()
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["router"]["repetitions"], 2)
        self.assertFalse(value["router"]["worker_outcomes_available"])
        self.assertFalse(value["pipeline_stage"]["authorized_before_router"])
        self.assertTrue(value["router"]["live_tokens_charged_to_routed_pipeline"])

    def test_task_profiles_qualification_and_scorer_are_hash_bound(self):
        value = self.load()
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        seed = ROOT / value["task"]["seed_root"]
        for relative, digest in value["task"]["seed_files_sha256"].items():
            self.assertEqual(hashlib.sha256((seed / relative).read_bytes()).hexdigest(), digest)
        for key in ("stage_l", "stage_s"):
            path = ROOT / value["task"][f"{key}_prompt"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["task"][f"{key}_prompt_sha256"])
        qualification = ROOT / value["qualification"]["path"]
        self.assertEqual(hashlib.sha256(qualification.read_bytes()).hexdigest(), value["qualification"]["sha256"])
        self.assertTrue(json.loads(qualification.read_text())["passed"])
        scorer = ROOT / value["provenance"]["scorer_path"]
        self.assertEqual(hashlib.sha256(scorer.read_bytes()).hexdigest(), value["provenance"]["scorer_sha256_at_freeze"])

    def test_router_parser_requires_exact_two_stage_route(self):
        stages = ["stage-L", "stage-S"]
        actions = ["neutral", "p000", "e1v2"]
        payload = json.dumps({"schema": "modus-long-horizon-p2a-router-decision-v1", "routes": [
            {"stage": "stage-L", "action": "p000", "reason": "local"},
            {"stage": "stage-S", "action": "e1v2", "reason": "reuse"},
        ]})
        self.assertEqual(_parse_decision(payload, stages, actions)["actions_by_stage"], {
            "stage-L": "p000", "stage-S": "e1v2",
        })
        with self.assertRaises(ValueError):
            _parse_decision(payload.replace('"e1v2"', '"p100"'), stages, actions)


if __name__ == "__main__":
    unittest.main()

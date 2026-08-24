import hashlib
import json
from pathlib import Path
import unittest

from scripts.score_modus_long_horizon_p2a_router import _parse_decision


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2a_agent_router_v1.json"
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-long-horizon-p2a-router-v1.json"


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

    def test_router_evidence_is_stable_and_still_outcome_blind(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertFalse(value["scientific_evidence"])
        self.assertTrue(value["outcome_blind_router_evidence"])
        self.assertEqual(value["stable_route"], {"stage-L": "p000", "stage-S": "e1v2"})
        self.assertEqual(value["execution"]["router_tokens_per_deployment"], 18894.5)
        self.assertTrue(value["decision"]["linked_pipeline_protocol_authorized"])
        for name, digest in (
            ("wave_result", "8ac98d545b50ab0563f1619f6138723f2577e552d8d4759c98754addb2ed960f"),
            ("score", "852be3c7fdcf55ce38d853610be4e0c159879256cd5dfd3a17e78dffbb14327f"),
        ):
            self.assertEqual(hashlib.sha256((ROOT / value["files"][name]).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()

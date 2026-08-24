import hashlib
import json
from pathlib import Path
import unittest

from scripts.score_modus_connectivity_p1f_router import _parse_decision, _usage_tokens


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_connectivity_p1f_agent_router_v1.json"
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-connectivity-p1f-agent-router-v1.json"


class ConnectivityP1fAgentRouterTest(unittest.TestCase):
    def load(self):
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_router_runs_before_workers_and_pays_live_cost(self):
        value = self.load()
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["model"]["local_slug"], "gpt-5.6-luna")
        self.assertEqual(value["model"]["reasoning_effort"], "max")
        self.assertEqual(value["router"]["repetitions"], 2)
        self.assertFalse(value["router"]["worker_outcomes_available"])
        self.assertFalse(value["worker_stage"]["authorized_before_router_outcome"])
        self.assertTrue(value["router"]["live_router_tokens_must_be_included_in_candidate_deployment_cost"])

    def test_router_task_profiles_and_qualification_are_hash_bound(self):
        value = self.load()
        prompt = ROOT / value["router"]["prompt"]
        self.assertEqual(hashlib.sha256(prompt.read_bytes()).hexdigest(), value["router"]["prompt_sha256"])
        for task in value["tasks"].values():
            worker_prompt = ROOT / task["worker_prompt"]
            self.assertEqual(hashlib.sha256(worker_prompt.read_bytes()).hexdigest(), task["worker_prompt_sha256"])
            for relative, digest in task["seed_files_sha256"].items():
                self.assertEqual(hashlib.sha256((ROOT / task["seed_root"] / relative).read_bytes()).hexdigest(), digest)
        for profile in value["profiles"].values():
            path = Path(profile["profile_path"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), profile["profile_sha256"])
        qualification = ROOT / value["qualification"]["path"]
        self.assertEqual(hashlib.sha256(qualification.read_bytes()).hexdigest(), value["qualification"]["sha256"])
        self.assertTrue(json.loads(qualification.read_text(encoding="utf-8"))["passed"])

    def test_calibration_and_router_scorer_are_bound(self):
        value = self.load()
        calibration = ROOT / value["candidate_calibration"]["path"]
        self.assertEqual(hashlib.sha256(calibration.read_bytes()).hexdigest(), value["candidate_calibration"]["sha256"])
        self.assertTrue(json.loads(calibration.read_text(encoding="utf-8"))["decision"]["new_holdout_design_authorized"])
        scorer = ROOT / value["provenance"]["router_scorer_path"]
        self.assertEqual(hashlib.sha256(scorer.read_bytes()).hexdigest(), value["provenance"]["router_scorer_sha256_at_freeze"])

    def test_router_response_parser_is_exact_and_profile_agnostic(self):
        tasks = ["connectivity-y01-perf-p1f", "connectivity-y02-perf-p1f"]
        actions = ["neutral", "p000", "e1v2"]
        payload = json.dumps({
            "schema": "modus-connectivity-p1f-router-decision-v1",
            "routes": [
                {"task_id": tasks[0], "action": "p000", "reason": "one batch"},
                {"task_id": tasks[1], "action": "e1v2", "reason": "reuse"},
            ],
        })
        parsed = _parse_decision(payload, tasks, actions)
        self.assertEqual(parsed["actions_by_task"], {tasks[0]: "p000", tasks[1]: "e1v2"})
        with self.assertRaises(ValueError):
            _parse_decision(payload.replace('"e1v2"', '"p100"'), tasks, actions)
        self.assertEqual(_usage_tokens({"input_tokens": 6, "output_tokens": 2}), 8)

    def test_outcome_blind_router_evidence_is_stable_and_hash_bound(self):
        value = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertFalse(value["scientific_evidence"])
        self.assertTrue(value["outcome_blind_router_evidence"])
        self.assertEqual(value["stable_route"], {
            "connectivity-y01-perf-p1f": "p000",
            "connectivity-y02-perf-p1f": "e1v2",
        })
        self.assertTrue(value["decision"]["worker_protocol_authorized"])
        self.assertFalse(value["decision"]["worker_protocol_frozen_before_outcomes"])
        for name, digest in (
            ("wave_result", "188f758a5583c4053fa80c8c37dba3982a3c7d9d6aa45977223c653df1c72a2a"),
            ("score", "271089cc37ed5c5a2dd8da8daebb6607ab95badd13713e5c2f01e9cd2b6aa00d"),
        ):
            self.assertEqual(hashlib.sha256((ROOT / value["files"][name]).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
from pathlib import Path
import unittest

from scripts.score_modus_reachability_p1e_p100_followup import _usage_tokens


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_reachability_luna_p1e_p100_followup_v1.json"
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-reachability-p1e-final-v1.json"


class ReachabilityLunaP1eP100FollowupTest(unittest.TestCase):
    def load(self):
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_followup_is_exactly_two_p100_x02_cells(self):
        value = self.load()
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["model"], {
            "local_slug": "gpt-5.6-luna",
            "reasoning_effort": "max",
            "authentication": "ChatGPT login",
        })
        self.assertEqual(value["matrix"]["actions"], ["p100"])
        self.assertEqual(value["matrix"]["tasks"], 1)
        self.assertEqual(value["matrix"]["cells"], 2)
        self.assertEqual(list(value["tasks"]), ["reachability-x02"])
        self.assertFalse(value["matrix"]["automatic_redispatch"])

    def test_parent_outcome_authorizes_followup_and_is_hash_bound(self):
        value = self.load()
        parent = value["parent_stage"]
        evidence = ROOT / parent["evidence_path"]
        score = ROOT / parent["score_path"]
        self.assertEqual(hashlib.sha256(evidence.read_bytes()).hexdigest(), parent["evidence_sha256"])
        self.assertEqual(hashlib.sha256(score.read_bytes()).hexdigest(), parent["score_sha256"])
        outcome = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(outcome["outcome"]["stage_decision"], "authorize_p100_follow_up_on_reachability_x02")
        self.assertFalse(outcome["outcome"]["third_pair_triggered"])

    def test_profile_task_and_tools_are_frozen(self):
        value = self.load()
        profile = Path(value["profile"]["profile_path"])
        self.assertEqual(hashlib.sha256(profile.read_bytes()).hexdigest(), value["profile"]["profile_sha256"])
        task = value["tasks"]["reachability-x02"]
        self.assertEqual(hashlib.sha256((ROOT / task["prompt"]).read_bytes()).hexdigest(), task["prompt_sha256"])
        for relative, digest in task["seed_files_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / task["seed_root"] / relative).read_bytes()).hexdigest(), digest)
        for path_key, hash_key in (("verifier_path", "verifier_sha256_at_freeze"), ("scorer_path", "scorer_sha256_at_freeze")):
            path = ROOT / value["provenance"][path_key]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["provenance"][hash_key])

    def test_followup_scoring_is_precommitted(self):
        scoring = self.load()["scoring"]
        self.assertEqual(scoring["performance_ratio_maximum"], 1.25)
        self.assertEqual(scoring["p100_token_advantage_minimum_vs_neutral"], 0.05)
        self.assertEqual(scoring["x01_action_frozen"], "p000")
        self.assertEqual(scoring["final_router_saving_minimum"], 0.15)
        self.assertEqual(_usage_tokens({"input_tokens": 10, "output_tokens": 2}), 12)

    def test_final_evidence_preserves_null_p100_and_mixed_route(self):
        value = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertFalse(value["scientific_evidence"])
        self.assertFalse(value["p100_followup"]["performance_eligible"])
        self.assertFalse(value["p100_followup"]["selected_for_x02"])
        self.assertEqual(value["final_route"]["actions_by_task"], {
            "reachability-x01": "p000", "reachability-x02": "neutral",
        })
        self.assertEqual(value["end_to_end_economics"]["break_even_deployments"], 15)
        self.assertFalse(value["conclusions"]["router_net_token_benefit_at_eight_deployments"])
        for name in ("p100_wave_result", "p100_manager_verification", "p100_score"):
            self.assertTrue((ROOT / value["files"][name]).is_file())
        score = ROOT / value["files"]["p100_score"]
        self.assertEqual(
            hashlib.sha256(score.read_bytes()).hexdigest(),
            "37ea17ee44d8a018bf96517de389e8050fe9f5253ef4beb0f3475a9a4c0ca041",
        )


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
from pathlib import Path
import unittest

from scripts.score_modus_connectivity_p1f_workers import _usage_tokens


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_connectivity_p1f_selected_workers_v1.json"


class ConnectivityP1fSelectedWorkersTest(unittest.TestCase):
    def load(self):
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_worker_matrix_is_derived_only_from_stable_agent_route(self):
        value = self.load()
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["tasks"]["connectivity-y01"]["actions"], ["neutral", "p000"])
        self.assertEqual(value["tasks"]["connectivity-y02"]["actions"], ["neutral", "e1v2"])
        self.assertEqual(value["matrix"]["cells"], 8)
        self.assertFalse(value["matrix"]["full_profile_matrix_completed"])
        self.assertFalse(value["matrix"]["automatic_redispatch"])

    def test_parent_router_is_stable_hash_bound_and_charged_live(self):
        value = self.load()
        parent = value["parent_router"]
        evidence = ROOT / parent["evidence_path"]
        score = ROOT / parent["score_path"]
        self.assertEqual(hashlib.sha256(evidence.read_bytes()).hexdigest(), parent["evidence_sha256"])
        self.assertEqual(hashlib.sha256(score.read_bytes()).hexdigest(), parent["score_sha256"])
        self.assertEqual(parent["stable_repetitions"], 2)
        self.assertEqual(parent["actions_by_task"], {"connectivity-y01": "p000", "connectivity-y02": "e1v2"})
        self.assertEqual(parent["tokens_per_deployment"], 15533.5)
        self.assertIn("15,533.5", value["scoring"]["end_to_end_cost"])

    def test_tasks_profiles_and_tools_remain_frozen(self):
        value = self.load()
        for profile in value["profiles"].values():
            path = Path(profile["profile_path"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), profile["profile_sha256"])
        for task in value["tasks"].values():
            self.assertEqual(hashlib.sha256((ROOT / task["prompt"]).read_bytes()).hexdigest(), task["prompt_sha256"])
            for relative, digest in task["seed_files_sha256"].items():
                self.assertEqual(hashlib.sha256((ROOT / task["seed_root"] / relative).read_bytes()).hexdigest(), digest)
        for path_key, hash_key in (("verifier_path", "verifier_sha256_at_freeze"), ("scorer_path", "scorer_sha256_at_freeze")):
            path = ROOT / value["provenance"][path_key]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["provenance"][hash_key])

    def test_quality_cost_and_economics_gates_are_precommitted(self):
        scoring = self.load()["scoring"]
        self.assertEqual(scoring["performance_ratio_maximum"], 1.25)
        self.assertEqual(scoring["minimum_selected_worker_token_saving_fraction"], 0.15)
        self.assertEqual(scoring["steady_relative_mad_maximum"], 0.10)
        self.assertEqual(_usage_tokens({"input_tokens": 9, "output_tokens": 1}), 10)


if __name__ == "__main__":
    unittest.main()

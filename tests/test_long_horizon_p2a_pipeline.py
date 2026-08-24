import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2a_pipeline_v1.json"


class LongHorizonP2aPipelineTest(unittest.TestCase):
    def load(self):
        return json.loads(PROTOCOL.read_text())

    def test_pipeline_is_linked_balanced_and_exactly_eight_workers(self):
        value = self.load()
        self.assertTrue(value["run_authorized"])
        self.assertTrue(value["execution"]["stage_s_uses_same_workspace_as_stage_l"])
        self.assertTrue(value["execution"]["stage_s_parent_record_required"])
        self.assertEqual(value["execution"]["worker_cells_if_complete"], 8)
        self.assertEqual(
            [(row["pair"], row["order"], row["arm"]) for row in value["pipelines"]],
            [(1, 1, "routed"), (1, 2, "neutral"), (2, 1, "neutral"), (2, 2, "routed")],
        )
        self.assertFalse(value["execution"]["automatic_redispatch"])

    def test_route_parent_profiles_prompts_and_tools_are_frozen(self):
        value = self.load()
        parent = value["parent_router"]
        for path_key, hash_key in (("evidence_path", "evidence_sha256"), ("score_path", "score_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / parent[path_key]).read_bytes()).hexdigest(), parent[hash_key])
        self.assertEqual(parent["actions"], {"stage-L": "p000", "stage-S": "e1v2"})
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        for stage in ("stage_l", "stage_s"):
            path = ROOT / value["task"][f"{stage}_prompt"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["task"][f"{stage}_prompt_sha256"])
        for path_key, hash_key in (
            ("pipeline_runner_path", "pipeline_runner_sha256_at_freeze"),
            ("stage_verifier_path", "stage_verifier_sha256_at_freeze"),
            ("pipeline_scorer_path", "pipeline_scorer_sha256_at_freeze"),
        ):
            self.assertEqual(
                hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(),
                value["provenance"][hash_key],
            )

    def test_quality_performance_cost_and_third_pair_rules_are_precommitted(self):
        scoring = self.load()["scoring"]
        self.assertEqual(scoring["performance_ratio_maximum"], 1.25)
        self.assertEqual(scoring["steady_relative_mad_maximum"], 0.10)
        self.assertEqual(scoring["minimum_worker_token_saving_fraction"], 0.15)
        self.assertEqual(scoring["third_pair_rule"]["near_threshold_band_inclusive"], [1.1875, 1.3125])
        self.assertIn("18,894.5", scoring["deployment_cost"])


if __name__ == "__main__":
    unittest.main()

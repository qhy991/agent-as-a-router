import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2i_first_pair_v1.json"


class LongHorizonP2iPairTest(unittest.TestCase):
    def test_agent_proposal_is_only_authorized_for_qualification(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["parent_router"]["actions"], {
            "stage-L": "p000", "stage-S": "e1v2",
        })
        self.assertFalse(value["parent_router"]["worker_deployment_authorized"])
        self.assertFalse(value["execution"]["deployment_worker_calls_authorized_before_score"])
        self.assertEqual(value["execution"]["qualification_worker_cells_if_complete"], 4)
        self.assertEqual(
            [(row["order"], row["arm"]) for row in value["pipelines"]],
            [(1, "proposed-route"), (2, "neutral")],
        )

    def test_common_gates_and_eight_deployment_horizon_are_frozen(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertEqual(value["expected_future_deployments"], 8)
        self.assertEqual(value["scoring"]["performance_ratio_maximum"], 1.25)
        self.assertEqual(value["scoring"]["steady_relative_mad_maximum"], 0.10)
        self.assertEqual(value["scoring"]["minimum_worker_token_saving_fraction"], 0.15)
        self.assertEqual(value["scoring"]["qualified_cached_router_tokens_per_deployment"], 0)
        self.assertFalse(value["execution"]["automatic_redispatch"])

    def test_profiles_prompts_router_result_and_tools_are_hash_bound(self):
        value = json.loads(PROTOCOL.read_text())
        for profile in value["profiles"].values():
            self.assertEqual(
                hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(),
                profile["profile_sha256"],
            )
        for stage in ("stage_l", "stage_s"):
            path = ROOT / value["task"][f"{stage}_prompt"]
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                value["task"][f"{stage}_prompt_sha256"],
            )
        for path_key, hash_key in (
            ("score_path", "score_sha256"),
            ("wave_result_path", "wave_result_sha256"),
        ):
            path = ROOT / value["parent_router"][path_key]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["parent_router"][hash_key])
        for path_key, hash_key in (
            ("pipeline_runner_path", "pipeline_runner_sha256"),
            ("stage_verifier_path", "stage_verifier_sha256"),
            ("scorer_path", "scorer_sha256_at_freeze"),
        ):
            path = ROOT / value["provenance"][path_key]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["provenance"][hash_key])


if __name__ == "__main__":
    unittest.main()

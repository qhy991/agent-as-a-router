import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2c_first_pair_v1.json"
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-long-horizon-p2c-transfer-v1.json"


class LongHorizonP2cPairTest(unittest.TestCase):
    def test_one_pair_order_gates_and_cost_are_frozen(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual([(p["order"], p["arm"]) for p in value["pipelines"]], [(1, "routed"), (2, "neutral")])
        self.assertEqual(value["execution"]["worker_cells_if_complete"], 4)
        self.assertEqual(value["scoring"]["performance_ratio_maximum"], 1.25)
        self.assertEqual(value["scoring"]["minimum_worker_token_saving_fraction"], 0.15)
        self.assertEqual(value["scoring"]["live_router_tokens_per_deployment"], 15951)
        self.assertEqual(value["expected_future_deployments"], 8)

    def test_route_profiles_prompts_and_tools_are_hash_bound(self):
        value = json.loads(PROTOCOL.read_text())
        parent = value["parent_router"]
        self.assertEqual(hashlib.sha256((ROOT / parent["score_path"]).read_bytes()).hexdigest(), parent["score_sha256"])
        self.assertEqual(parent["actions"], {"stage-L": "p000", "stage-S": "e1v2"})
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        for stage in ("stage_l", "stage_s"):
            path = ROOT / value["task"][f"{stage}_prompt"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["task"][f"{stage}_prompt_sha256"])
        for path_key, hash_key in (
            ("pipeline_runner_path", "pipeline_runner_sha256"),
            ("stage_verifier_path", "stage_verifier_sha256"),
            ("scorer_path", "scorer_sha256_at_freeze"),
        ):
            self.assertEqual(
                hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(),
                value["provenance"][hash_key],
            )

    def test_transfer_replicates_utility_but_not_eight_deployment_economics(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertTrue(value["prospective_low_acquisition_transfer_evidence"])
        self.assertTrue(value["stopping_rule"]["stopped_after_first_pair"])
        self.assertEqual(value["primary_economics"]["break_even_deployments"], 10)
        self.assertEqual(value["primary_economics"]["net_tokens_at_expected_deployments"], -118237)
        self.assertTrue(value["cross_contract_conclusion"]["p2b_and_p2c_both_reduce_worker_and_live_router_deployment_tokens"])
        self.assertFalse(value["cross_contract_conclusion"]["live_agent_net_positive_at_eight_on_both"])
        for name, hash_key in (("router_score", "router_score_sha256"), ("execution_summary", "execution_summary_sha256"), ("score", "score_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["files"][name]).read_bytes()).hexdigest(), value["files"][hash_key])


if __name__ == "__main__":
    unittest.main()

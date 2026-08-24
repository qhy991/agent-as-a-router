import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2d_second_pair_v1.json"
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-long-horizon-p2d-final-v1.json"

class LongHorizonP2dReplicationTest(unittest.TestCase):
    def test_reverse_second_pair_and_cached_cost_are_frozen(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertTrue(value["post_outcome_replication"])
        self.assertEqual([(p["order"], p["arm"]) for p in value["pipelines"]], [(1, "neutral"), (2, "routed")])
        self.assertEqual(value["arms"]["routed"]["stage-L"], "e1v2")
        self.assertEqual(value["arms"]["routed"]["stage-S"], "p000")
        self.assertEqual(value["parent_router"]["cached_tokens_per_deployment"], 0)
        self.assertTrue(value["scoring"]["no_further_replication"])
        parent = value["parent_initial"]
        for path_key, hash_key in (("evidence_path", "evidence_sha256"), ("score_path", "score_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / parent[path_key]).read_bytes()).hexdigest(), parent[hash_key])
        for path_key, hash_key in (("pipeline_runner_path", "pipeline_runner_sha256"), ("stage_verifier_path", "stage_verifier_sha256"), ("scorer_path", "scorer_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(), value["provenance"][hash_key])

    def test_final_evidence_rejects_exactly_cached_bad_route(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertTrue(value["prospective_cached_routing_negative_evidence"])
        self.assertTrue(value["conclusions"]["cache_identity_and_zero_model_replay_work"])
        self.assertFalse(value["conclusions"]["agent_selected_route_is_cost_performance_qualified"])
        self.assertTrue(value["conclusions"]["exact_cache_can_reliably_replay_a_bad_route"])
        self.assertFalse(value["cache_entry_disposition"]["deployment_qualified"])
        self.assertIsNone(value["economics"]["break_even_deployments"])
        self.assertEqual(value["economics"]["net_tokens_at_expected_deployments"], -1310165)
        for name, hash_key in (("second_execution", "second_execution_sha256"), ("second_score", "second_score_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["files"][name]).read_bytes()).hexdigest(), value["files"][hash_key])

if __name__ == "__main__": unittest.main()

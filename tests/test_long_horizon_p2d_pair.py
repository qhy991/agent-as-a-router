import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2d_cached_pair_v1.json"

class LongHorizonP2dPairTest(unittest.TestCase):
    def test_reverse_route_cache_and_primary_cost_are_frozen(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["arms"]["routed"], {"stage-L": "e1v2", "stage-S": "p000", "live_router_calls_per_deployment": 0})
        self.assertTrue(value["cache"]["zero_model_replay_passed"])
        self.assertEqual(value["cache"]["replayed_actions"], value["parent_router"]["actions"])
        self.assertEqual(value["parent_router"]["cached_tokens_per_deployment"], 0)
        self.assertEqual(value["scoring"]["live_agent_counterfactual_tokens_per_deployment"], 20788)
        self.assertEqual(value["execution"]["worker_cells_if_complete"], 4)

    def test_files_profiles_and_tools_are_bound(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertEqual(hashlib.sha256((ROOT / value["cache"]["entry_path"]).read_bytes()).hexdigest(), value["cache"]["entry_sha256"])
        self.assertEqual(hashlib.sha256((ROOT / value["parent_router"]["score_path"]).read_bytes()).hexdigest(), value["parent_router"]["score_sha256"])
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        for path_key, hash_key in (("pipeline_runner_path", "pipeline_runner_sha256"), ("stage_verifier_path", "stage_verifier_sha256"), ("scorer_path", "scorer_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(), value["provenance"][hash_key])

if __name__ == "__main__": unittest.main()

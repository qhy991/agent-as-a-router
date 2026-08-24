import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2a_third_pair_v1.json"


class LongHorizonP2aReplicationTest(unittest.TestCase):
    def load(self):
        return json.loads(PROTOCOL.read_text())

    def test_third_pair_is_post_outcome_hash_ordered_and_four_workers(self):
        value = self.load()
        self.assertTrue(value["run_authorized"])
        self.assertTrue(value["post_outcome_replication"])
        self.assertEqual(value["order_selection"]["first_nibble"], "1")
        self.assertEqual(value["order_selection"]["selected_order"], ["neutral", "routed"])
        self.assertEqual(value["execution"]["worker_cells_if_complete"], 4)
        self.assertFalse(value["execution"]["automatic_redispatch"])

    def test_actions_gates_parent_and_tools_are_frozen(self):
        value = self.load()
        self.assertEqual(value["arms"]["routed"], {"stage-L": "p000", "stage-S": "e1v2", "live_router_calls_per_deployment": 1})
        self.assertEqual(value["scoring"]["performance_ratio_maximum"], 1.25)
        self.assertEqual(value["scoring"]["minimum_worker_token_saving_fraction"], 0.15)
        self.assertTrue(value["scoring"]["no_further_replication"])
        parent = value["parent_initial"]
        for path_key, hash_key in (("evidence_path", "evidence_sha256"), ("score_path", "score_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / parent[path_key]).read_bytes()).hexdigest(), parent[hash_key])
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        for path_key, hash_key in (
            ("pipeline_runner_path", "pipeline_runner_sha256"),
            ("stage_verifier_path", "stage_verifier_sha256"),
            ("scorer_path", "scorer_sha256_at_freeze"),
        ):
            self.assertEqual(
                hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(),
                value["provenance"][hash_key],
            )


if __name__ == "__main__":
    unittest.main()

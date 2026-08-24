import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2d_second_pair_v1.json"

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

if __name__ == "__main__": unittest.main()

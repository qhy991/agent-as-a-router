import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2k_second_pair_v1.json"


class LongHorizonP2kReplicationTest(unittest.TestCase):
    def test_reversed_pair_and_noise_resolution_are_frozen(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertTrue(value["post_outcome_replication"])
        self.assertEqual(
            [(row["order"], row["arm"]) for row in value["pipelines"]],
            [(1, "neutral"), (2, "proposed-route")],
        )
        self.assertEqual(value["arms"]["proposed-route"]["stage-L"], "p000v2")
        self.assertEqual(value["arms"]["proposed-route"]["stage-S"], "e1v2")
        self.assertTrue(value["scoring"]["per_repetition_performance_required"])
        self.assertTrue(value["scoring"]["no_further_replication"])

    def test_parent_profiles_and_tools_are_hash_bound(self):
        value = json.loads(PROTOCOL.read_text())
        for profile in value["profiles"].values():
            self.assertEqual(
                hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(),
                profile["profile_sha256"],
            )
        parent = value["parent_initial"]
        for path_key, hash_key in (("evidence_path", "evidence_sha256"), ("score_path", "score_sha256")):
            self.assertEqual(
                hashlib.sha256((ROOT / parent[path_key]).read_bytes()).hexdigest(),
                parent[hash_key],
            )
        for path_key, hash_key in (("pipeline_runner_path", "pipeline_runner_sha256"), ("stage_verifier_path", "stage_verifier_sha256"), ("scorer_path", "scorer_sha256")):
            self.assertEqual(
                hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(),
                value["provenance"][hash_key],
            )


if __name__ == "__main__":
    unittest.main()

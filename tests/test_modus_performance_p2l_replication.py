import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_performance_p2l_second_triplet_v1.json"


class ModusPerformanceP2lReplicationTest(unittest.TestCase):
    def test_reversed_triplet_and_candidate_specific_gates_are_frozen(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertTrue(value["post_outcome_replication"])
        self.assertEqual([row["profile"] for row in value["cells"]], ["e1v2", "e1v3", "neutral"])
        self.assertTrue(value["scoring"]["e1v3_requires_two_valid_repetitions"])
        self.assertTrue(value["scoring"]["e1v3_requires_per_repetition_performance"])
        self.assertTrue(value["scoring"]["no_further_replication"])

    def test_parent_profiles_and_tools_are_hash_bound(self):
        value = json.loads(PROTOCOL.read_text())
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        parent = value["parent_initial"]
        for path_key, hash_key in (("evidence_path", "evidence_sha256"), ("score_path", "score_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / parent[path_key]).read_bytes()).hexdigest(), parent[hash_key])
        for path_key, hash_key in (("runner_path", "runner_sha256"), ("verifier_path", "verifier_sha256"), ("scorer_path", "scorer_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(), value["provenance"][hash_key])


if __name__ == "__main__":
    unittest.main()

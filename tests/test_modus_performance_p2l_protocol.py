import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_performance_p2l_triplet_v1.json"


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


class ModusPerformanceP2lProtocolTest(unittest.TestCase):
    def test_three_profiles_and_order_are_frozen_before_outcomes(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual([row["profile"] for row in value["cells"]], ["neutral", "e1v3", "e1v2"])
        self.assertEqual(value["execution"]["worker_cells_if_complete"], 3)
        self.assertFalse(value["execution"]["automatic_redispatch"])
        self.assertEqual(value["expected_future_deployments"], 8)

    def test_joint_gates_and_objective_selection_are_frozen(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertEqual(value["scoring"]["performance_ratio_to_neutral_maximum"], 1.25)
        self.assertEqual(value["scoring"]["steady_relative_mad_maximum"], 0.10)
        self.assertEqual(value["scoring"]["minimum_token_saving_fraction_vs_neutral"], 0.15)
        self.assertEqual(value["scoring"]["selection"], "among eligible e1v2 and e1v3, choose lower Worker tokens")

    def test_task_profiles_and_tools_are_hash_bound(self):
        value = json.loads(PROTOCOL.read_text())
        seed = ROOT / value["task"]["seed_root"]
        self.assertEqual(_tree_sha256(seed), value["task"]["seed_tree_sha256"])
        for path_key, hash_key in (("prompt", "prompt_sha256"), ("qualification_path", "qualification_sha256")):
            path = ROOT / value["task"][path_key]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["task"][hash_key])
        self.assertTrue(json.loads((ROOT / value["task"]["qualification_path"]).read_text())["passed"])
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        for path_key, hash_key in (("runner_path", "runner_sha256"), ("verifier_path", "verifier_sha256"), ("scorer_path", "scorer_sha256_at_freeze")):
            path = ROOT / value["provenance"][path_key]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["provenance"][hash_key])


if __name__ == "__main__":
    unittest.main()

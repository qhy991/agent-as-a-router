import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_invariant_specialization_calibration.json"


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


class ModusInvariantSpecializationCalibrationTest(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(PROTOCOL.read_text())

    def test_complete_counterbalanced_development_matrix(self):
        value = self.value
        self.assertTrue(value["run_authorized"])
        self.assertTrue(value["development_only"])
        self.assertEqual(len(value["cells"]), 24)
        expected = {
            (task, strategy, repetition)
            for task in value["tasks"]
            for strategy in value["strategies"]
            for repetition in (1, 2)
        }
        self.assertEqual(
            {
                (cell["task_id"], cell["strategy"], cell["repetition"])
                for cell in value["cells"]
            },
            expected,
        )
        for task in value["tasks"]:
            first = [
                cell["strategy"] for cell in value["cells"]
                if cell["task_id"] == task and cell["repetition"] == 1
            ]
            second = [
                cell["strategy"] for cell in value["cells"]
                if cell["task_id"] == task and cell["repetition"] == 2
            ]
            self.assertEqual(second, list(reversed(first)))
        self.assertFalse(value["provenance"]["a800_dispatch_authorized"])
        self.assertTrue(value["execution"]["no_post_outcome_arms"])

    def test_tasks_and_tools_are_hash_bound(self):
        value = self.value
        for task in value["tasks"].values():
            self.assertEqual(
                tree_sha256(ROOT / task["seed_root"]),
                task["seed_tree_sha256"],
            )
            self.assertEqual(
                hashlib.sha256((ROOT / task["prompt"]).read_bytes()).hexdigest(),
                task["prompt_sha256"],
            )
        for section, path_key, hash_key in (
            ("qualification", "path", "sha256"),
            ("execution", "runner", "runner_sha256"),
            ("execution", "verifier", "verifier_sha256"),
            ("execution", "custody_wrapper", "custody_wrapper_sha256"),
            ("execution", "custody_qualification", "custody_qualification_sha256"),
            ("scoring", "scorer", "scorer_sha256"),
        ):
            self.assertEqual(
                hashlib.sha256((ROOT / value[section][path_key]).read_bytes()).hexdigest(),
                value[section][hash_key],
            )
        self.assertTrue(
            json.loads((ROOT / value["qualification"]["path"]).read_text())["passed"]
        )

    def test_strategy_paths_are_semantic_and_repository_relative(self):
        for strategy_id, strategy in self.value["strategies"].items():
            self.assertIn(strategy_id, strategy["artifact_path"])
            self.assertFalse(Path(strategy["artifact_path"]).is_absolute())
            self.assertEqual(strategy["artifact_repository"], "dsh-personal-plugins")
            self.assertRegex(strategy["artifact_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            self.value["strategies"]["invariant-specialized-optimization"]["status"],
            "unqualified-development-candidate",
        )

    def test_scoring_cannot_promote_utility(self):
        scoring = self.value["scoring"]
        self.assertEqual(scoring["candidate_correctness_required"], "8/8")
        self.assertEqual(scoring["candidate_topology_required"], "8/8")
        self.assertEqual(
            scoring["candidate_target_invariants_absent_required"],
            "at least 7/8",
        )
        self.assertIn("diagnostic only", scoring["performance_and_tokens"])


if __name__ == "__main__":
    unittest.main()

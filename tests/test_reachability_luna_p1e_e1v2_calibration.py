import hashlib
import json
from pathlib import Path
import unittest

from scripts.score_modus_reachability_p1e_e1v2_calibration import _usage_tokens


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_reachability_luna_p1e_e1v2_calibration_v1.json"


class ReachabilityLunaP1eE1v2CalibrationTest(unittest.TestCase):
    def load(self):
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_calibration_is_development_only_and_exactly_four_cells(self):
        value = self.load()
        self.assertTrue(value["run_authorized"])
        self.assertTrue(value["development_only"])
        self.assertEqual(value["matrix"]["actions"], ["neutral", "e1v2"])
        self.assertEqual(value["matrix"]["tasks"], 1)
        self.assertEqual(value["matrix"]["repetitions_per_action"], 2)
        self.assertEqual(value["matrix"]["cells"], 4)
        self.assertFalse(value["matrix"]["automatic_redispatch"])

    def test_candidate_is_existing_unqualified_single_axis_profile(self):
        value = self.load()
        candidate = value["profiles"]["e1v2"]
        profile = Path(candidate["profile_path"])
        text = profile.read_text(encoding="utf-8")
        self.assertEqual(candidate["bits"], "E1/T0/A0")
        self.assertEqual(candidate["qualification_status"], "unqualified-development-candidate")
        self.assertEqual(hashlib.sha256(profile.read_bytes()).hexdigest(), candidate["profile_sha256"])
        self.assertIn("invoke that helper once for each reusable input", text)
        self.assertIn("target consume the prepared representation", text)
        self.assertIn("Do not merely call the helper inside the target", text)

    def test_task_parent_and_tools_are_hash_bound(self):
        value = self.load()
        task = value["tasks"]["reachability-x02"]
        self.assertEqual(hashlib.sha256((ROOT / task["prompt"]).read_bytes()).hexdigest(), task["prompt_sha256"])
        for relative, digest in task["seed_files_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / task["seed_root"] / relative).read_bytes()).hexdigest(), digest)
        parent = ROOT / value["parent_outcome"]["path"]
        self.assertEqual(hashlib.sha256(parent.read_bytes()).hexdigest(), value["parent_outcome"]["sha256"])
        for path_key, hash_key in (("verifier_path", "verifier_sha256_at_freeze"), ("scorer_path", "scorer_sha256_at_freeze")):
            path = ROOT / value["provenance"][path_key]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["provenance"][hash_key])

    def test_calibration_gates_are_precommitted(self):
        scoring = self.load()["scoring"]
        self.assertEqual(scoring["performance_ratio_maximum"], 1.25)
        self.assertEqual(scoring["steady_relative_mad_maximum"], 0.10)
        self.assertIn("non-raw prepared representation", scoring["semantic_mechanism"])
        self.assertEqual(_usage_tokens({"input_tokens": 4, "output_tokens": 3}), 7)


if __name__ == "__main__":
    unittest.main()

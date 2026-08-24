import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_reachability_luna_p1e_v1.json"


class ReachabilityLunaP1eTaskTest(unittest.TestCase):
    def load(self):
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_protocol_is_frozen_for_luna_max(self):
        value = self.load()
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["model"]["local_slug"], "gpt-5.6-luna")
        self.assertEqual(value["model"]["reasoning_effort"], "max")
        self.assertEqual(value["expected_future_deployments"], 8)
        self.assertFalse(value["harness"]["automatic_redispatch"])

    def test_first_stage_is_exactly_eight_neutral_p000_cells(self):
        value = self.load()
        self.assertEqual(value["matrix"]["actions"], ["neutral", "p000"])
        self.assertEqual(value["matrix"]["repetitions_per_action"], 2)
        self.assertEqual(value["matrix"]["tasks"], 2)
        self.assertEqual(value["matrix"]["cells"], 8)
        self.assertIn("not in stage one", value["matrix"]["p100_follow_up"])

    def test_prompts_and_seed_files_are_hash_bound(self):
        value = self.load()
        for task_name, task in value["tasks"].items():
            prompt = ROOT / task["prompt"]
            self.assertEqual(hashlib.sha256(prompt.read_bytes()).hexdigest(), task["prompt_sha256"])
            seed = ROOT / task["seed_root"]
            present = sorted(
                str(path.relative_to(seed)) for path in seed.rglob("*") if path.is_file()
            )
            self.assertEqual(present, sorted(task["seed_files_sha256"]))
            for relative, digest in task["seed_files_sha256"].items():
                self.assertEqual(hashlib.sha256((seed / relative).read_bytes()).hexdigest(), digest)
            public_prompt = " ".join(prompt.read_text(encoding="utf-8").lower().split())
            self.assertNotIn("single batch", public_prompt)
            self.assertNotIn("ninety-six", public_prompt)
            self.assertIn(task_name.replace("reachability-", "perf_reachability_"), public_prompt)

    def test_task_qualification_and_tooling_are_bound(self):
        value = self.load()
        provenance = value["provenance"]
        qualification = ROOT / provenance["task_qualification_path"]
        self.assertEqual(hashlib.sha256(qualification.read_bytes()).hexdigest(), provenance["task_qualification_sha256"])
        report = json.loads(qualification.read_text(encoding="utf-8"))
        self.assertTrue(report["passed"])
        self.assertEqual(report["task_count"], 2)
        for task in report["tasks"]:
            self.assertTrue(task["passed"])
            self.assertEqual(task["variants"]["local"]["benchmark"]["rounds"], 9)
            self.assertEqual(task["variants"]["coordinated"]["benchmark"]["rounds"], 9)
        for script, field in (
            (ROOT / "scripts/verify_modus_reachability_prospective.py", "verifier_sha256_at_freeze"),
            (ROOT / "scripts/score_modus_reachability_prospective.py", "scorer_sha256_at_freeze"),
        ):
            self.assertEqual(hashlib.sha256(script.read_bytes()).hexdigest(), provenance[field])

    def test_scoring_and_ambiguity_rules_are_precommitted(self):
        scoring = self.load()["scoring"]
        self.assertEqual(scoring["performance_ratio_maximum"], 1.25)
        self.assertEqual(scoring["minimum_p000_token_saving_fraction_per_task"], 0.15)
        self.assertEqual(scoring["third_pair_rule"]["near_threshold_band_inclusive"], [1.1875, 1.3125])
        self.assertEqual(scoring["third_pair_rule"]["steady_relative_mad_maximum"], 0.10)


if __name__ == "__main__":
    unittest.main()

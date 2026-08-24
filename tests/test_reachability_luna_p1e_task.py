import hashlib
import json
from pathlib import Path
import unittest

from scripts.verify_modus_reachability_p1e_corrected import _parse_benchmark_output


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_reachability_luna_p1e_v1.json"
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-reachability-p1e-stage1-v1.json"


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

    def test_corrected_verifier_parses_multiline_and_legacy_benchmarks(self):
        self.assertEqual(
            _parse_benchmark_output('{\n  "rounds": 9,\n  "steady_seconds": 0.1\n}\n')["rounds"],
            9,
        )
        self.assertEqual(_parse_benchmark_output("{'seconds': 0.2}\n")["seconds"], 0.2)

    def test_stage_one_evidence_is_hash_bound_and_authorizes_only_p100(self):
        value = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertFalse(value["scientific_evidence"])
        self.assertEqual(value["execution"]["valid_execution_cells"], 8)
        self.assertTrue(value["result"]["profile_task_interaction_observed"])
        self.assertEqual(value["outcome"]["stage_decision"], "authorize_p100_follow_up_on_reachability_x02")
        self.assertFalse(value["outcome"]["third_pair_triggered"])
        self.assertEqual(value["router_signal"]["actions_by_task"], {
            "reachability-x01": "p000", "reachability-x02": "neutral",
        })
        for name in ("wave_result", "manager_verification", "score"):
            path = ROOT / value["files"][name]
            self.assertTrue(path.is_file())
        score = ROOT / value["files"]["score"]
        self.assertEqual(hashlib.sha256(score.read_bytes()).hexdigest(), value["files"]["score_sha256"])
        corrected = ROOT / value["verifier_correction"]["corrected_verifier_path"]
        self.assertEqual(
            hashlib.sha256(corrected.read_bytes()).hexdigest(),
            value["verifier_correction"]["corrected_verifier_sha256"],
        )


if __name__ == "__main__":
    unittest.main()

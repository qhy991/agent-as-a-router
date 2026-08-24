import hashlib
import json
from pathlib import Path
import unittest

from scripts.score_modus_reachability_prospective import _performance_gate


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_reachability_prospective_v1.json"
BASE = ROOT / "examples/modus_profile_router/reachability-prospective-v1"


class ReachabilityProspectiveTaskTest(unittest.TestCase):
    def load(self):
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_protocol_is_frozen_and_authorized(self):
        value = self.load()
        self.assertTrue(value["run_authorized"])
        self.assertEqual(
            value["schema"], "acrouter-modus-reachability-prospective-protocol-v1"
        )
        self.assertEqual(value["model"]["local_slug"], "gpt-5.3-codex-spark")
        self.assertFalse(value["harness"]["automatic_redispatch"])
        self.assertTrue(value["failure_policy"]["no_model_substitution"])
        self.assertFalse(value["failure_policy"]["post_hoc_task_or_gate_change"])

    def test_matrix_is_neutral_p000_only_with_no_p100_follow_up(self):
        value = self.load()
        self.assertEqual(value["matrix"]["actions"], ["neutral", "p000"])
        self.assertEqual(value["matrix"]["repetitions_per_action"], 2)
        self.assertEqual(value["matrix"]["cells"], 8)
        self.assertEqual(
            value["matrix"]["p100_follow_up"],
            "not scheduled; p000 pass stops data acquisition",
        )

    def test_profiles_and_prompts_are_hash_bound(self):
        value = self.load()
        self.assertEqual(
            value["profiles"]["p000"]["profile_sha256"],
            "4430eff8d5b732333319f93bf0a699c3593f6e6d708296d304c76c7161f67282",
        )
        self.assertEqual(
            value["profiles"]["neutral"]["profile_sha256"],
            hashlib.sha256(b"").hexdigest(),
        )
        for name, task in value["tasks"].items():
            text = (ROOT / task["prompt"]).read_text(encoding="utf-8")
            self.assertEqual(
                hashlib.sha256(text.encode()).hexdigest(),
                task["prompt_sha256"],
            )
            normalized = " ".join(text.split())
            package = name.replace("reachability-", "perf_reachability_")
            self.assertIn(f"{package}/target.py", text)
            self.assertIn("Do not use web search", normalized)
            self.assertIn("Do not modify tests", text)

    def test_seed_files_match_frozen_hashes_and_run_clean(self):
        value = self.load()
        for name, task in value["tasks"].items():
            seed_root = ROOT / task["seed_root"]
            present = sorted(
                str(path.relative_to(seed_root))
                for path in seed_root.rglob("*")
                if path.is_file()
            )
            self.assertEqual(present, sorted(task["seed_files_sha256"]))
            for relative, digest in task["seed_files_sha256"].items():
                raw = (seed_root / relative).read_bytes()
                self.assertEqual(
                    hashlib.sha256(raw).hexdigest(),
                    digest,
                    f"{name}/{relative} drifted from the frozen seed",
                )

    def test_expected_local_topology_names_only_the_target_module(self):
        value = self.load()
        for name, task in value["tasks"].items():
            package = name.replace("reachability-", "perf_reachability_")
            self.assertEqual(task["expected_local_paths"], [f"{package}/target.py"])

    def test_staged_policy_bounds_are_pre_committed(self):
        value = self.load()
        staged = value["staged_policy_under_test"]
        self.assertIn("before any outcome", value["purpose"])
        self.assertEqual(
            staged["classification"],
            "prospective replication of the post-outcome staged neutral/p000-first replay",
        )
        self.assertEqual(value["provenance"]["replayed_staged_break_even_deployments"], 8)
        self.assertEqual(value["scoring"]["promotion_gate"].split()[-1], "0.15")

    def test_performance_gate_is_absolute_one_point_two_five(self):
        self.assertTrue(_performance_gate(1.25))
        self.assertFalse(_performance_gate(1.250001))
        self.assertFalse(_performance_gate(1.91))


if __name__ == "__main__":
    unittest.main()

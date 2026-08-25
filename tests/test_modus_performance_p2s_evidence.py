import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-performance-p2s-fresh-transfer-v1.json"


class P2sEvidenceTest(unittest.TestCase):
    def test_fresh_instance_route_is_valid_and_task_dependent(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertEqual(value["formal_status"], "valid_profile_task_interaction_and_exact_router_but_not_economic_at_8")
        self.assertEqual(value["execution"]["valid_worker_cells"], 9)
        self.assertEqual(value["execution"]["correct_worker_cells"], 9)
        self.assertEqual(value["execution"]["automatic_redispatches"], 0)
        self.assertEqual(value["execution"]["web_search_items"], 0)
        self.assertEqual(value["router"]["exact_matches"], 3)
        self.assertEqual(value["router"]["selected_distinct_profiles"], 2)
        self.assertEqual(value["task_results"]["keyed-closest-negative"]["selected_profile"], "p000v2")
        self.assertEqual(value["task_results"]["keyed-distinct-quartic-sum"]["selected_profile"], "e1v3")
        self.assertEqual(value["task_results"]["rotate-mix32"]["selected_profile"], "p000v2")

    def test_quality_passes_but_eight_deployment_economics_fail(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertTrue(value["decision"]["worker_route_quality_qualified"])
        self.assertFalse(value["decision"]["deployment_authorized"])
        self.assertGreater(value["deployment"]["worker_saving_fraction_vs_best_eligible_fixed"], 0.40)
        self.assertLess(value["deployment"]["worst_selected_ratio_to_fastest_correct"], 1.25)
        self.assertEqual(value["economics"]["break_even_deployments"], 13)
        self.assertLess(value["economics"]["net_tokens_at_8_deployments"], 0)

    def test_raw_structured_files_and_predispatch_failure_are_bound(self):
        value = json.loads(EVIDENCE.read_text())
        for path, expected in value["files"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)
        failure = json.loads((ROOT / "examples/modus_profile_router/performance-p2s-v1/predispatch-apparatus-failure.json").read_text())
        self.assertEqual(failure["model_calls"], 0)
        self.assertEqual(failure["usage_tokens"], 0)
        self.assertFalse(failure["scientific_evidence"])


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import unittest

from scripts.build_modus_experiment_scorecard import build


ROOT = Path(__file__).resolve().parents[1]
SCORECARD = ROOT / "agentic-artifacts/modus-experiment-scorecard-v1.json"


class ModusExperimentScorecardTest(unittest.TestCase):
    def test_checked_in_view_equals_canonical_artifacts(self):
        self.assertEqual(json.loads(SCORECARD.read_text()), build(ROOT))

    def test_invalid_p2h_is_visible_but_excluded(self):
        value = json.loads(SCORECARD.read_text())
        rows = {row["experiment"]: row for row in value["experiments"]}
        self.assertFalse(rows["P2h"]["outcome_valid"])
        self.assertTrue(rows["P2h"]["excluded_from_valid_trends"])
        self.assertIsNone(rows["P2h"]["net_tokens_at_8_deployments"])
        self.assertEqual(value["summary"]["valid_outcomes"], 13)
        self.assertEqual(value["summary"]["qualified_routes"], 8)
        self.assertEqual(value["summary"]["net_positive_at_8_deployments"], 3)

    def test_valid_negative_p2i_keeps_saving_but_blocks_economics(self):
        value = json.loads(SCORECARD.read_text())
        rows = {row["experiment"]: row for row in value["experiments"]}
        self.assertTrue(rows["P2i"]["outcome_valid"])
        self.assertFalse(rows["P2i"]["route_qualified"])
        self.assertGreater(rows["P2i"]["worker_saving_fraction"], 0.40)
        self.assertIsNone(rows["P2i"]["break_even_deployments"])
        self.assertIsNone(rows["P2i"]["net_tokens_at_8_deployments"])

    def test_p2j_profile_revision_is_jointly_eligible_and_economic(self):
        value = json.loads(SCORECARD.read_text())
        rows = {row["experiment"]: row for row in value["experiments"]}
        self.assertTrue(rows["P2j"]["outcome_valid"])
        self.assertTrue(rows["P2j"]["route_qualified"])
        self.assertGreater(rows["P2j"]["worker_saving_fraction"], 0.40)
        self.assertLess(rows["P2j"]["final_performance_ratio_to_fastest"], 1.25)
        self.assertGreater(rows["P2j"]["net_tokens_at_8_deployments"], 0)

    def test_p2k_keeps_cost_signal_but_rejects_unstable_long_horizon_route(self):
        value = json.loads(SCORECARD.read_text())
        rows = {row["experiment"]: row for row in value["experiments"]}
        self.assertTrue(rows["P2k"]["outcome_valid"])
        self.assertFalse(rows["P2k"]["route_qualified"])
        self.assertGreater(rows["P2k"]["worker_saving_fraction"], 0.40)
        self.assertGreater(rows["P2k"]["final_performance_ratio_to_fastest"], 1.25)
        self.assertIsNone(rows["P2k"]["net_tokens_at_8_deployments"])

    def test_p2l_improves_representation_but_fails_strict_joint_gate(self):
        value = json.loads(SCORECARD.read_text())
        rows = {row["experiment"]: row for row in value["experiments"]}
        self.assertTrue(rows["P2l"]["outcome_valid"])
        self.assertFalse(rows["P2l"]["route_qualified"])
        self.assertGreater(rows["P2l"]["worker_saving_fraction"], 0.30)
        self.assertLess(rows["P2l"]["final_performance_ratio_to_fastest"], 1.0)
        self.assertIsNone(rows["P2l"]["net_tokens_at_8_deployments"])

    def test_p2n_preserves_two_task_preference_but_excludes_contaminated_direct_task(self):
        value = json.loads(SCORECARD.read_text())
        rows = {row["experiment"]: row for row in value["experiments"]}
        self.assertTrue(rows["P2n"]["outcome_valid"])
        self.assertFalse(rows["P2n"]["route_qualified"])
        self.assertGreater(rows["P2n"]["worker_saving_fraction"], 0.25)
        self.assertLess(rows["P2n"]["net_tokens_at_8_deployments"], 0)
        self.assertIn("custody", rows["P2n"]["disqualification"])

    def test_p2p_restores_direct_task_under_read_custody(self):
        value=json.loads(SCORECARD.read_text());rows={r["experiment"]:r for r in value["experiments"]};self.assertTrue(rows["P2p"]["outcome_valid"]);self.assertTrue(rows["P2p"]["route_qualified"]);self.assertGreater(rows["P2p"]["worker_saving_fraction"],0.90);self.assertGreater(rows["P2p"]["net_tokens_at_8_deployments"],0)

    def test_p2s_validates_fresh_instance_route_but_not_eight_deployment_economics(self):
        value = json.loads(SCORECARD.read_text())
        rows = {row["experiment"]: row for row in value["experiments"]}
        row = rows["P2s"]
        self.assertTrue(row["outcome_valid"])
        self.assertTrue(row["route_qualified"])
        self.assertGreater(row["worker_saving_fraction"], 0.40)
        self.assertLess(row["final_performance_ratio_to_fastest"], 1.25)
        self.assertEqual(row["break_even_deployments"], 13)
        self.assertLess(row["net_tokens_at_8_deployments"], 0)


if __name__ == "__main__":
    unittest.main()

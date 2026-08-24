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
        self.assertEqual(value["summary"]["valid_outcomes"], 9)
        self.assertEqual(value["summary"]["qualified_routes"], 6)
        self.assertEqual(value["summary"]["net_positive_at_8_deployments"], 2)

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


if __name__ == "__main__":
    unittest.main()

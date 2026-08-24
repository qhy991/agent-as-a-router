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
        self.assertEqual(value["summary"]["valid_outcomes"], 6)
        self.assertEqual(value["summary"]["qualified_routes"], 5)
        self.assertEqual(value["summary"]["net_positive_at_8_deployments"], 1)


if __name__ == "__main__":
    unittest.main()

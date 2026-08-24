import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-long-horizon-p2h-invalid-v1.json"


class LongHorizonP2hInvalidEvidenceTest(unittest.TestCase):
    def test_invalid_run_cannot_promote_or_authorize_followup(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertEqual(value["formal_status"], "invalid_apparatus")
        self.assertFalse(value["scientific_evidence"])
        self.assertFalse(value["conclusions"]["route_qualified"])
        self.assertFalse(value["conclusions"]["deployment_authorized"])
        self.assertFalse(value["invalidity"]["second_pair_authorized"])
        self.assertEqual(
            value["invalidity"]["classification"],
            "uncontracted_hidden_representation_requirement",
        )

    def test_exploratory_metrics_are_retained_but_not_promoted(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertGreater(value["exploratory_only"]["worker_token_saving_fraction"], 0.60)
        self.assertGreater(value["exploratory_only"]["stage_l_proposed_ratio_to_fastest"], 10)
        self.assertGreater(value["exploratory_only"]["final_proposed_ratio_to_fastest"], 4)
        self.assertEqual(
            value["conclusions"]["profile_route_reduces_tokens"],
            "exploratory_not_scientific",
        )

    def test_every_named_evidence_file_is_hash_bound(self):
        value = json.loads(EVIDENCE.read_text())
        files = value["files"]
        for key, path in files.items():
            if key.endswith("_sha256"):
                continue
            expected = files[key + "_sha256"]
            actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, key)


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "agentic-artifacts/modus-profile-experience-transfer-result.json"


class ModusProfileExperienceTransferEvidenceTest(unittest.TestCase):
    def test_formal_router_applies_experience_but_transfer_quality_fails(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertEqual(value["formal_status"], "valid_quality_failure")
        self.assertTrue(value["formalization"]["router_agent_policy_explicitly_injected"])
        self.assertFalse(value["formalization"]["agent_visible_historical_codenames"])
        self.assertEqual(value["router"]["experience_application_matches"], "3/3")
        self.assertEqual(value["execution"]["valid_worker_cells"], 5)
        self.assertEqual(value["execution"]["correct_worker_cells"], 5)
        self.assertFalse(value["deployment"]["quality_qualified"])
        self.assertFalse(value["conclusions"]["accumulated_experience_transfers_with_quality"])

    def test_raw_economics_cannot_authorize_failed_quality(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertGreater(value["deployment"]["raw_saving_fraction"], 0.35)
        self.assertGreater(
            value["economics"]["marginal"]["raw_net_tokens_at_8_deployments"], 0
        )
        self.assertEqual(
            value["economics"]["marginal"]["qualified_decision"],
            "defer_correctness",
        )
        self.assertFalse(value["decision"]["deployment_authorized"])
        self.assertFalse(value["decision"]["post_outcome_replication_authorized"])
        self.assertGreater(
            value["task_results"]["direct-bit-transformation"]["performance_ratio"],
            1.25,
        )

    def test_every_structured_source_is_hash_bound(self):
        value = json.loads(EVIDENCE.read_text())
        for path, digest in value["files"].items():
            self.assertEqual(
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                digest,
            )
        self.assertEqual(
            hashlib.sha256((ROOT / value["protocol"]["path"]).read_bytes()).hexdigest(),
            value["protocol"]["sha256"],
        )


if __name__ == "__main__":
    unittest.main()

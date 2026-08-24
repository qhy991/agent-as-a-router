import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_evidence_gated_agent_live_v1.json"

class ModusEvidenceGatedAgentLiveProtocolTest(unittest.TestCase):
    def test_two_cells_dispatch_and_abstain_are_frozen(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual([(c["id"], c["expected"]) for c in value["cases"]], [("qualified-p2b", "dispatch"), ("rejected-p2d", "abstain")])
        self.assertFalse(value["execution"]["workers_authorized"])
        self.assertFalse(value["execution"]["automatic_redispatch"])
        for case in value["cases"]:
            self.assertEqual(hashlib.sha256((ROOT / case["prompt"]).read_bytes()).hexdigest(), case["prompt_sha256"])
            self.assertEqual(hashlib.sha256((ROOT / case["qualification_path"]).read_bytes()).hexdigest(), case["qualification_sha256"])
        scorer = ROOT / value["provenance"]["scorer_path"]
        self.assertEqual(hashlib.sha256(scorer.read_bytes()).hexdigest(), value["provenance"]["scorer_sha256"])

if __name__ == "__main__": unittest.main()

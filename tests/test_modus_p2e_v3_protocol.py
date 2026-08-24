import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_p2e_autonomous_agent_v3.json"
EVIDENCE = ROOT / "agentic-artifacts/modus-p2e-autonomous-evidence-gated-agent-v3.json"

class ModusP2eV3ProtocolTest(unittest.TestCase):
    def test_agent_facing_view_uses_dispatch_and_abstain_only(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertFalse(value["execution"]["workers_authorized"])
        view = json.loads((ROOT / value["candidate_view"]).read_text())
        self.assertEqual([row["resolution"]["decision"] for row in view["stages"]], ["dispatch", "abstain"])
        self.assertEqual(hashlib.sha256((ROOT / value["candidate_view"]).read_bytes()).hexdigest(), value["candidate_view_sha256"])
        self.assertEqual(hashlib.sha256((ROOT / value["prompt"]).read_bytes()).hexdigest(), value["prompt_sha256"])
        for path_key, hash_key in (("view_builder", "view_builder_sha256"), ("scorer", "scorer_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(), value["provenance"][hash_key])

    def test_live_agent_selects_derived_candidate_and_abstains_empty_stage(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertTrue(value["live_autonomous_candidate_derivation_evidence"])
        self.assertEqual(value["live_agent"]["qualified_stage"]["decision"], "dispatch")
        self.assertEqual(value["live_agent"]["qualified_stage"]["profile"], "e1v2")
        self.assertEqual(value["live_agent"]["unqualified_stage"]["decision"], "abstain")
        self.assertEqual(value["live_agent"]["strict_validation"], "pass")
        self.assertEqual(value["live_agent"]["workers_called"], 0)
        self.assertFalse(value["failure_lineage"]["previous_runs_retried_or_overwritten"])
        for name, hash_key in (("wave_result", "wave_result_sha256"), ("score", "score_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["files"][name]).read_bytes()).hexdigest(), value["files"][hash_key])

if __name__ == "__main__": unittest.main()

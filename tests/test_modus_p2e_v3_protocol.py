import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_p2e_autonomous_agent_v3.json"

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

if __name__ == "__main__": unittest.main()

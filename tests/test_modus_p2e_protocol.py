import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_p2e_autonomous_agent_v1.json"

class ModusP2eProtocolTest(unittest.TestCase):
    def test_candidate_view_is_derived_and_protocol_is_worker_free(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertFalse(value["execution"]["workers_authorized"])
        self.assertEqual(hashlib.sha256((ROOT / value["candidate_view"]).read_bytes()).hexdigest(), value["candidate_view_sha256"])
        view = json.loads((ROOT / value["candidate_view"]).read_text())
        self.assertEqual([row["resolution"]["decision"] for row in view["stages"]], ["dispatch", "defer"])
        self.assertEqual(hashlib.sha256((ROOT / value["registry"]).read_bytes()).hexdigest(), value["registry_sha256"])
        self.assertEqual(hashlib.sha256((ROOT / value["descriptors"]).read_bytes()).hexdigest(), value["descriptors_sha256"])
        for path_key, hash_key in (("view_builder", "view_builder_sha256"), ("scorer", "scorer_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(), value["provenance"][hash_key])

if __name__ == "__main__": unittest.main()

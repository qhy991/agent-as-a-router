import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_completed_lifecycle_p2g_v1.json"

class ModusCompletedLifecycleP2gTest(unittest.TestCase):
    def test_request_resolution_authorizes_one_continuation_without_router(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["execution"]["continuation_worker_cells"], 1)
        self.assertEqual(value["execution"]["router_calls"], 0)
        self.assertEqual(value["execution"]["neutral_fallbacks"], 0)
        self.assertEqual(value["expected_lifecycle"]["status"], "complete")
        self.assertTrue(value["expected_lifecycle"]["complete"])
        for path_key, hash_key in (("previous_lifecycle", "previous_lifecycle_sha256"), ("qualification_resolution", "qualification_resolution_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value[path_key]).read_bytes()).hexdigest(), value[hash_key])
        worker = value["continuation_worker"]
        for path_key, hash_key in (("prompt", "prompt_sha256"), ("parent_verification", "parent_verification_sha256"), ("parent_record", "parent_record_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / worker[path_key]).read_bytes()).hexdigest(), worker[hash_key])
        for path_key, hash_key in (("stage_verifier", "stage_verifier_sha256"), ("scorer", "scorer_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(), value["provenance"][hash_key])

if __name__ == "__main__": unittest.main()

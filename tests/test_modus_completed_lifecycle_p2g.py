import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_completed_lifecycle_p2g_v1.json"
EVIDENCE = ROOT / "agentic-artifacts/modus-completed-lifecycle-p2g-live-v1.json"

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

    def test_live_continuation_closes_partial_lifecycle(self):
        value = json.loads(EVIDENCE.read_text())
        self.assertTrue(value["live_qualification_resolution_evidence"])
        self.assertEqual(value["offline_qualification"]["resolution_status"], "accepted")
        self.assertEqual(value["offline_qualification"]["router_model_calls"], 0)
        self.assertTrue(value["continuation_worker"]["correctness_passed"])
        self.assertEqual(value["continuation_worker"]["tokens"], 171176)
        self.assertEqual(value["completed_lifecycle"]["pending_qualification_requests"], 0)
        self.assertEqual(value["completed_lifecycle"]["status"], "complete")
        self.assertTrue(value["completed_lifecycle"]["complete"])
        for name, hash_key in (("wave_result", "wave_result_sha256"), ("qualified_verification", "qualified_verification_sha256"), ("lifecycle_result", "lifecycle_result_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["files"][name]).read_bytes()).hexdigest(), value["files"][hash_key])

if __name__ == "__main__": unittest.main()

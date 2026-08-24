import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_partial_lifecycle_p2f_v1.json"

class ModusPartialLifecycleP2fTest(unittest.TestCase):
    def test_only_qualified_worker_is_authorized_and_lifecycle_stays_partial(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["execution"]["qualified_worker_cells"], 1)
        self.assertEqual(value["execution"]["unqualified_worker_cells"], 0)
        self.assertEqual(value["execution"]["neutral_fallbacks"], 0)
        self.assertFalse(value["qualification_request"]["worker_authorized"])
        self.assertEqual(value["expected_lifecycle"]["status"], "partial_pending_qualification")
        self.assertFalse(value["expected_lifecycle"]["complete"])

    def test_plan_parent_request_profile_and_tools_are_hash_bound(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertEqual(hashlib.sha256((ROOT / value["dispatch_plan"]["path"]).read_bytes()).hexdigest(), value["dispatch_plan"]["sha256"])
        worker = value["qualified_worker"]
        parent_root = ROOT / worker["parent_workspace"]
        tree = hashlib.sha256()
        for path in sorted(parent_root.rglob("*")):
            if path.is_file():
                tree.update(str(path.relative_to(parent_root)).encode() + b"\0" + path.read_bytes() + b"\0")
        self.assertEqual(tree.hexdigest(), worker["parent_tree_sha256"])
        for path_key, hash_key in (("prompt", "prompt_sha256"), ("parent_verification", "parent_verification_sha256"), ("parent_record", "parent_record_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / worker[path_key]).read_bytes()).hexdigest(), worker[hash_key])
        self.assertEqual(hashlib.sha256(Path(worker["profile_path"]).read_bytes()).hexdigest(), worker["profile_sha256"])
        request = value["qualification_request"]
        self.assertEqual(hashlib.sha256((ROOT / request["path"]).read_bytes()).hexdigest(), request["sha256"])
        for path_key, hash_key in (("stage_verifier", "stage_verifier_sha256"), ("scorer", "scorer_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(), value["provenance"][hash_key])

if __name__ == "__main__": unittest.main()

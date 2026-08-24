import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];PROTOCOL=ROOT/"configs/modus_p2o_read_custody_canary_v1.json"
class ModusP2oCustodyProtocolTest(unittest.TestCase):
 def test_canary_is_frozen_fail_closed(self):
  v=json.loads(PROTOCOL.read_text());self.assertTrue(v["run_authorized"]);self.assertEqual(v["execution"]["cells"],1);self.assertFalse(v["execution"]["automatic_redispatch"]);self.assertEqual(v["expected"],{"current_workspace_read":"allowed","sibling_workspace_read":"denied","owner_repo_read":"denied"})
 def test_task_wrapper_wave_and_parent_are_bound(self):
  v=json.loads(PROTOCOL.read_text());self.assertEqual(hashlib.sha256((ROOT/v["task"]["path"]).read_bytes()).hexdigest(),v["task"]["sha256"]);self.assertEqual(hashlib.sha256((ROOT/v["execution"]["wrapper"]).read_bytes()).hexdigest(),v["provenance"]["wrapper_sha256"]);self.assertEqual(hashlib.sha256((ROOT/"src/acrouter_repro/codex_spark_wave.py").read_bytes()).hexdigest(),v["provenance"]["wave_owner_sha256"]);self.assertEqual(hashlib.sha256((ROOT/v["parent_defect"]["path"]).read_bytes()).hexdigest(),v["parent_defect"]["sha256"])
if __name__=="__main__":unittest.main()

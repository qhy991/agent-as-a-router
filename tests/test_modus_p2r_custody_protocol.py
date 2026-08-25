import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];P=ROOT/"configs/modus_p2r_all_temp_custody_canary_v1.json"
class P2rProtocolTest(unittest.TestCase):
 def test_all_four_read_classes_frozen(self):
  v=json.loads(P.read_text());self.assertTrue(v["run_authorized"]);self.assertEqual(v["expected"],{"current_workspace":"allowed","sibling_workspace":"denied","historical_tmp":"denied","owner_repo":"denied"});self.assertFalse(v["execution"]["automatic_redispatch"])
 def test_task_wrapper_and_parent_bound(self):
  v=json.loads(P.read_text());self.assertEqual(hashlib.sha256((ROOT/v["task"]["path"]).read_bytes()).hexdigest(),v["task"]["sha256"]);self.assertEqual(hashlib.sha256((ROOT/v["execution"]["wrapper"]).read_bytes()).hexdigest(),v["execution"]["wrapper_sha256"]);self.assertEqual(hashlib.sha256((ROOT/v["parent"]["p2o_pass"]).read_bytes()).hexdigest(),v["parent"]["p2o_pass_sha256"]);self.assertEqual(hashlib.sha256((ROOT/v["parent"]["p2n_defect"]).read_bytes()).hexdigest(),v["parent"]["p2n_defect_sha256"])
if __name__=="__main__":unittest.main()

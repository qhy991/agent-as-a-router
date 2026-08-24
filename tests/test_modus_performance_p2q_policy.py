import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];P=ROOT/"configs/modus_performance_p2q_policy_v1.json"
class P2qPolicyTest(unittest.TestCase):
 def test_router_and_complete_matrix_frozen_together(self):
  v=json.loads(P.read_text());self.assertTrue(v["run_authorized"]);self.assertFalse(v["router"]["worker_outcomes_available"]);self.assertEqual(len(v["cells"]),9);self.assertEqual({(c["task"],c["profile"]) for c in v["cells"]},{(t,p) for t in v["tasks"] for p in v["profiles"]});self.assertTrue(v["execution"]["no_followup_replication"])
 def test_profiles_custody_qualification_and_tools_bound(self):
  v=json.loads(P.read_text())
  for r in v["profiles"].values():self.assertEqual(hashlib.sha256(Path(r["profile_path"]).read_bytes()).hexdigest(),r["profile_sha256"])
  for sec,key,hkey in (("router","prompt","prompt_sha256"),("router","scorer","scorer_sha256"),("qualification","path","sha256"),("execution","custody_wrapper","custody_wrapper_sha256"),("provenance","runner","runner_sha256"),("provenance","verifier","verifier_sha256"),("provenance","matrix_scorer","matrix_scorer_sha256")):
   self.assertEqual(hashlib.sha256((ROOT/v[sec][key]).read_bytes()).hexdigest(),v[sec][hkey])
if __name__=="__main__":unittest.main()

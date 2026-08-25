import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];P=ROOT/"configs/modus_performance_p2s_policy_v1.json"
def _tree_sha256(root):
 d=hashlib.sha256()
 for p in sorted(root.rglob("*")):
  if p.is_file():d.update(p.relative_to(root).as_posix().encode()+b"\0"+p.read_bytes()+b"\0")
 return d.hexdigest()
class P2sPolicyTest(unittest.TestCase):
 def test_router_and_complete_matrix_frozen_together(self):
  v=json.loads(P.read_text());self.assertTrue(v["run_authorized"]);self.assertFalse(v["router"]["worker_outcomes_available"]);self.assertEqual(len(v["cells"]),9);self.assertEqual({(c["task"],c["profile"]) for c in v["cells"]},{(t,p) for t in v["tasks"] for p in v["profiles"]});self.assertTrue(v["execution"]["no_followup_replication"])
 def test_profiles_custody_qualification_and_tools_bound(self):
  v=json.loads(P.read_text())
  for r in v["profiles"].values():self.assertEqual(hashlib.sha256(Path(r["profile_path"]).read_bytes()).hexdigest(),r["profile_sha256"])
  for task in v["tasks"].values():self.assertEqual(_tree_sha256(ROOT/task["seed_root"]),task["seed_tree_sha256"])
  for sec,key,hkey in (("router","prompt","prompt_sha256"),("router","scorer","scorer_sha256"),("qualification","path","sha256"),("execution","custody_wrapper","custody_wrapper_sha256"),("execution","custody_qualification_evidence","custody_qualification_evidence_sha256"),("provenance","runner","runner_sha256"),("provenance","verifier","verifier_sha256"),("provenance","matrix_scorer","matrix_scorer_sha256")):
   self.assertEqual(hashlib.sha256((ROOT/v[sec][key]).read_bytes()).hexdigest(),v[sec][hkey])
  self.assertTrue(json.loads((ROOT/v["qualification"]["path"]).read_text())["passed"])
  self.assertEqual(json.loads((ROOT/v["execution"]["custody_qualification_evidence"]).read_text())["formal_status"],"pass")
if __name__=="__main__":unittest.main()

import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];P=ROOT/"configs/modus_performance_p2p_agent_router_v1.json"
class P2pRouterTest(unittest.TestCase):
 def test_frozen_and_bound(self):
  v=json.loads(P.read_text());self.assertTrue(v["run_authorized"]);self.assertFalse(v["router"]["worker_outcomes_available"]);self.assertFalse(v["router"]["deployment_authorized"])
  for sec,key,hkey in (("task","prompt","prompt_sha256"),("task","qualification","qualification_sha256"),("custody","wrapper","wrapper_sha256"),("custody","qualification_evidence","qualification_evidence_sha256"),("provenance","scorer","scorer_sha256")):
   self.assertEqual(hashlib.sha256((ROOT/v[sec][key]).read_bytes()).hexdigest(),v[sec][hkey])
if __name__=="__main__":unittest.main()

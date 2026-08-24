import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];P=ROOT/"configs/modus_performance_p2p_triplet_v1.json"
class P2pTripletTest(unittest.TestCase):
 def test_triplet_is_complete_custody_confined_and_frozen(self):
  v=json.loads(P.read_text());self.assertEqual([c["profile"] for c in v["cells"]],["neutral","p000v2","e1v3"]);self.assertTrue(v["execution"]["no_followup_replication"]);self.assertEqual(v["parent_router"]["action"],"p000v2")
  for sec,key,hkey in (("execution","custody_wrapper","custody_wrapper_sha256"),("parent_router","score_path","score_sha256"),("parent_router","wave_path","wave_sha256"),("provenance","runner","runner_sha256"),("provenance","verifier","verifier_sha256"),("provenance","scorer","scorer_sha256")):
   self.assertEqual(hashlib.sha256((ROOT/v[sec][key]).read_bytes()).hexdigest(),v[sec][hkey])
if __name__=="__main__":unittest.main()

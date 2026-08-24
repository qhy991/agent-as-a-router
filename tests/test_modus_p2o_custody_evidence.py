import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];E=ROOT/"agentic-artifacts/modus-p2o-read-custody-canary-v5.json"
class ModusP2oCustodyEvidenceTest(unittest.TestCase):
 def test_live_canary_allows_current_and_denies_external_content(self):
  v=json.loads(E.read_text());self.assertEqual(v["formal_status"],"pass");self.assertTrue(all(v["checks"].values()));self.assertTrue(v["authorization"]["custody_confined_experiment_infrastructure"]);self.assertFalse(v["authorization"]["retroactive_p2n_direct_validation"])
 def test_files_are_hash_bound(self):
  v=json.loads(E.read_text());f=v["files"]
  for k,p in f.items():
   if not k.endswith("_sha256"):self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),f[k+"_sha256"])
if __name__=="__main__":unittest.main()

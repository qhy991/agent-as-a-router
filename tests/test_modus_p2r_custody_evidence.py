import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];E=ROOT/"agentic-artifacts/modus-p2r-all-temp-custody-canary-v1.json"
class P2rEvidenceTest(unittest.TestCase):
 def test_passes_all_read_classes(self):
  v=json.loads(E.read_text());self.assertEqual(v["formal_status"],"pass");self.assertTrue(all(v["checks"].values()));self.assertTrue(v["authorization"]["all_temp_confined_future_experiments"]);self.assertFalse(v["authorization"]["p2q_retroactive_validation"])
 def test_files_bound(self):
  v=json.loads(E.read_text());f=v["files"]
  for k,p in f.items():
   if not k.endswith("_sha256"):self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),f[k+"_sha256"])
if __name__=="__main__":unittest.main()

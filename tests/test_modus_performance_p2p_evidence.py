import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];E=ROOT/"agentic-artifacts/modus-codex-luna-max-performance-p2p-positive-v1.json"
class P2pEvidenceTest(unittest.TestCase):
 def test_valid_custody_confined_selection(self):
  v=json.loads(E.read_text());self.assertEqual(v["formal_status"],"valid_positive");self.assertTrue(v["custody_confined"]);self.assertEqual(v["router"]["action"],"p000v2");self.assertTrue(v["router"]["matches_selected_profile"]);self.assertGreater(v["profiles"]["p000v2"]["token_saving_fraction"],0.90);self.assertGreater(v["economics"]["net_tokens_at_8_deployments"],0)
 def test_files_bound(self):
  v=json.loads(E.read_text());f=v["files"]
  for k,p in f.items():
   if not k.endswith("_sha256"):self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),f[k+"_sha256"])
if __name__=="__main__":unittest.main()

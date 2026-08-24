import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];EVIDENCE=ROOT/"agentic-artifacts/modus-codex-luna-max-performance-p2n-partial-v1.json"
class ModusPerformanceP2nEvidenceTest(unittest.TestCase):
 def test_two_task_preference_is_preserved_and_direct_is_excluded(self):
  v=json.loads(EVIDENCE.read_text());self.assertEqual(v["formal_status"],"partial_valid_custody_exclusion");self.assertEqual(v["conclusions"]["agent_matches_valid_constrained_oracle"],"2/2");self.assertTrue(v["conclusions"]["two_task_types_select_different_profiles"]);self.assertFalse(v["conclusions"]["three_way_preference_matrix_is_valid"]);self.assertEqual(v["excluded_tasks"],["affine-checksum"])
 def test_raw_full_matrix_economics_are_retracted(self):
  v=json.loads(EVIDENCE.read_text());self.assertFalse(v["decision"]["deployment_authorized"]);self.assertLess(v["partial_two_task_economics"]["net_tokens_at_8_deployments"],0);self.assertIn("full-matrix",v["custody_exclusion"]["invalidated_claims"][2])
 def test_files_are_hash_bound(self):
  v=json.loads(EVIDENCE.read_text());f=v["files"]
  for k,p in f.items():
   if not k.endswith("_sha256"):self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),f[k+"_sha256"])
if __name__=="__main__":unittest.main()

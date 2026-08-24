import hashlib,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1];PROTOCOL=ROOT/"configs/modus_performance_p2n_matrix_v1.json"
class ModusPerformanceP2nMatrixTest(unittest.TestCase):
 def test_complete_symmetric_matrix_and_gates(self):
  v=json.loads(PROTOCOL.read_text());self.assertTrue(v["run_authorized"]);self.assertEqual(len(v["cells"]),9);self.assertEqual({(c["task"],c["profile"]) for c in v["cells"]},{(t,p) for t in v["tasks"] for p in v["profiles"]});self.assertTrue(v["execution"]["no_followup_replication"]);self.assertEqual(v["scoring"]["performance_ratio_to_neutral_maximum"],1.25);self.assertEqual(v["scoring"]["minimum_token_saving_fraction_vs_neutral"],0.15)
 def test_profiles_router_and_tools_are_hash_bound(self):
  v=json.loads(PROTOCOL.read_text())
  for r in v["profiles"].values():self.assertEqual(hashlib.sha256(Path(r["profile_path"]).read_bytes()).hexdigest(),r["profile_sha256"])
  for key,hkey in (("score_path","score_sha256"),("wave_result_path","wave_result_sha256")):
   r=v["parent_router"];self.assertEqual(hashlib.sha256((ROOT/r[key]).read_bytes()).hexdigest(),r[hkey])
  for key,hkey in (("runner_path","runner_sha256"),("verifier_path","verifier_sha256"),("scorer_path","scorer_sha256")):
   r=v["provenance"];self.assertEqual(hashlib.sha256((ROOT/r[key]).read_bytes()).hexdigest(),r[hkey])
if __name__=="__main__":unittest.main()

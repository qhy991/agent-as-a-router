import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_connectivity_p1f_third_pair_replication_v1.json"
EVIDENCE = ROOT / "agentic-artifacts/modus-codex-luna-max-connectivity-p1f-replicated-v1.json"


class ConnectivityP1fReplicationTest(unittest.TestCase):
    def load(self):
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_replication_is_explicitly_post_outcome_and_four_cells(self):
        value = self.load()
        self.assertTrue(value["run_authorized"])
        self.assertTrue(value["post_outcome_replication"])
        self.assertEqual(value["matrix"]["cells"], 4)
        self.assertEqual(value["matrix"]["repetitions_per_action"], 1)
        self.assertFalse(value["matrix"]["automatic_redispatch"])
        self.assertEqual(value["scoring"]["combine_with_initial"], "three repetitions per action after adding this pair")

    def test_actions_gates_and_router_cost_are_unchanged(self):
        value = self.load()
        self.assertEqual(value["tasks"]["connectivity-y01"]["actions"], ["neutral", "p000"])
        self.assertEqual(value["tasks"]["connectivity-y02"]["actions"], ["neutral", "e1v2"])
        self.assertEqual(value["scoring"]["performance_ratio_maximum"], 1.25)
        self.assertEqual(value["scoring"]["minimum_selected_worker_token_saving_fraction"], 0.15)
        self.assertEqual(value["scoring"]["router_tokens_per_deployment"], 15533.5)

    def test_parent_inputs_profiles_prompts_and_tools_are_hash_bound(self):
        value = self.load()
        parent = value["parent_initial"]
        for path_key, hash_key in (
            ("evidence_path", "evidence_sha256"),
            ("worker_protocol_path", "worker_protocol_sha256"),
            ("manager_verification_path", "manager_verification_sha256"),
        ):
            self.assertEqual(hashlib.sha256((ROOT / parent[path_key]).read_bytes()).hexdigest(), parent[hash_key])
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        for task in value["tasks"].values():
            self.assertEqual(hashlib.sha256((ROOT / task["prompt"]).read_bytes()).hexdigest(), task["prompt_sha256"])
        for path_key, hash_key in (("verifier_path", "verifier_sha256_at_freeze"), ("scorer_path", "scorer_sha256_at_freeze")):
            self.assertEqual(
                hashlib.sha256((ROOT / value["provenance"][path_key]).read_bytes()).hexdigest(),
                value["provenance"][hash_key],
            )

    def test_replicated_evidence_preserves_route_but_rejects_eight_deployments(self):
        value = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertFalse(value["scientific_evidence"])
        self.assertTrue(value["replicated_preliminary_evidence"])
        self.assertTrue(value["conclusions"]["agent_router_matches_constrained_oracle"])
        self.assertTrue(value["conclusions"]["router_plus_worker_reduces_per_deployment_tokens"])
        self.assertFalse(value["conclusions"]["router_plus_worker_net_positive_at_eight_deployments"])
        self.assertEqual(value["economics"]["break_even_deployments"], 10)
        self.assertEqual(value["economics"]["net_tokens_at_expected_deployments"], -424028)
        for name, hash_key in (
            ("replication_wave_result", "replication_wave_result_sha256"),
            ("replication_manager_verification", "replication_manager_verification_sha256"),
            ("replication_score", "replication_score_sha256"),
        ):
            self.assertEqual(
                hashlib.sha256((ROOT / value["files"][name]).read_bytes()).hexdigest(),
                value["files"][hash_key],
            )


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
from pathlib import Path
import unittest

from acrouter_repro.modus_route_cache import build_key, load_cached_route

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2d_agent_cache_v1.json"

class LongHorizonP2dCacheProtocolTest(unittest.TestCase):
    def test_cache_must_replay_before_workers(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["router"]["repetitions"], 1)
        self.assertTrue(value["cache_gate"]["zero_model_exact_replay_before_workers"])
        self.assertFalse(value["pipeline_stage"]["authorized_before_cache_replay"])
        self.assertEqual(value["cache_gate"]["future_cached_router_tokens_per_deployment"], 0)
        self.assertEqual(value["pipeline_stage"]["frozen_first_pair_order"], ["routed", "neutral"])

    def test_frozen_inputs_and_prior_cache_mechanism(self):
        value = json.loads(PROTOCOL.read_text())
        for profile in value["profiles"].values():
            self.assertEqual(hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(), profile["profile_sha256"])
        for key in ("stage_l", "stage_s"):
            path = ROOT / value["task"][f"{key}_prompt"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), value["task"][f"{key}_prompt_sha256"])
        seed = ROOT / value["task"]["seed_root"]
        tree = hashlib.sha256()
        for path in sorted(seed.rglob("*")):
            if path.is_file():
                tree.update(str(path.relative_to(seed)).encode() + b"\0" + path.read_bytes() + b"\0")
        self.assertEqual(tree.hexdigest(), value["task"]["seed_tree_sha256"])
        prior = ROOT / value["cache_gate"]["prior_mechanism_evidence"]
        self.assertEqual(hashlib.sha256(prior.read_bytes()).hexdigest(), value["cache_gate"]["prior_mechanism_evidence_sha256"])
        owner = ROOT / "src/acrouter_repro/modus_route_cache.py"
        self.assertEqual(hashlib.sha256(owner.read_bytes()).hexdigest(), value["provenance"]["route_cache_owner_sha256"])

    def test_actual_p2d_entry_replays_reverse_linked_route_zero_model(self):
        config = json.loads((ROOT / "configs/modus_p2d_route_cache_v1.json").read_text())
        key = build_key(
            task_contract_sha256=config["task_contract_sha256"],
            typed_descriptor=config["typed_descriptor"],
            router_prompt_sha256=config["router_prompt_sha256"],
            model_slug=config["model"]["slug"],
            reasoning_effort=config["model"]["reasoning_effort"],
            allowed_actions=config["allowed_actions"],
            profile_digests=config["profile_digests"],
        )
        result = load_cached_route(
            ROOT / "examples/modus_profile_router/long-horizon-p2d-v1/route-cache.json",
            current_key=key,
            evidence_root=ROOT,
        )
        self.assertEqual(result["actions_by_stage"], {"stage-L": "e1v2", "stage-S": "p000"})
        self.assertEqual(result["router_model_calls"], 0)
        self.assertEqual(result["router_tokens"], 0)

if __name__ == "__main__": unittest.main()

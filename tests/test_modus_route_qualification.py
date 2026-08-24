import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from acrouter_repro.modus_route_cache import build_key
from acrouter_repro.modus_route_qualification import (
    RouteQualificationError,
    load_qualified_cached_route,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY = {
    "performance_ratio_maximum": 1.25,
    "relative_mad_maximum": 0.10,
    "minimum_token_saving_fraction": 0.15,
}


def key_from_config(name: str):
    value = json.loads((ROOT / f"configs/modus_{name}_route_cache_v1.json").read_text())
    return build_key(
        task_contract_sha256=value["task_contract_sha256"],
        typed_descriptor=value["typed_descriptor"],
        router_prompt_sha256=value["router_prompt_sha256"],
        model_slug=value["model"]["slug"],
        reasoning_effort=value["model"]["reasoning_effort"],
        allowed_actions=value["allowed_actions"],
        profile_digests=value["profile_digests"],
    )


class ModusRouteQualificationTest(unittest.TestCase):
    def test_p2b_qualified_envelope_allows_zero_model_deployment(self):
        result = load_qualified_cached_route(
            entry_path=ROOT / "examples/modus_profile_router/long-horizon-p2b-v1/route-cache.json",
            current_key=key_from_config("p2b"),
            envelope_path=ROOT / "examples/modus_profile_router/long-horizon-p2b-v1/route-qualification.json",
            evidence_root=ROOT,
            current_policy=POLICY,
        )
        self.assertEqual(result["actions_by_stage"], {"stage-L": "p000", "stage-S": "e1v2"})
        self.assertTrue(result["deployment_qualified"])
        self.assertEqual(result["router_model_calls"], 0)
        self.assertEqual(result["router_tokens"], 0)

    def test_p2d_rejected_envelope_denies_exact_cache_hit(self):
        with self.assertRaises(RouteQualificationError):
            load_qualified_cached_route(
                entry_path=ROOT / "examples/modus_profile_router/long-horizon-p2d-v1/route-cache.json",
                current_key=key_from_config("p2d"),
                envelope_path=ROOT / "examples/modus_profile_router/long-horizon-p2d-v1/route-qualification.json",
                evidence_root=ROOT,
                current_policy=POLICY,
            )

    def _mutated_p2b_envelope(self, mutate):
        source = ROOT / "examples/modus_profile_router/long-horizon-p2b-v1/route-qualification.json"
        value = json.loads(source.read_text())
        mutate(value)
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "envelope.json"
        path.write_text(json.dumps(value))
        return temporary, path

    def test_route_evidence_policy_and_status_tampering_fail_closed(self):
        mutations = [
            lambda value: value["route_actions"].update({"stage-S": "neutral"}),
            lambda value: value.update({"outcome_evidence_sha256": "f" * 64}),
            lambda value: value.update({"outcome_evidence_path": "missing.json"}),
            lambda value: value.update({"status": "rejected"}),
        ]
        for index, mutation in enumerate(mutations):
            temporary, path = self._mutated_p2b_envelope(mutation)
            try:
                with self.subTest(index=index), self.assertRaises(RouteQualificationError):
                    load_qualified_cached_route(
                        entry_path=ROOT / "examples/modus_profile_router/long-horizon-p2b-v1/route-cache.json",
                        current_key=key_from_config("p2b"), envelope_path=path,
                        evidence_root=ROOT, current_policy=POLICY,
                    )
            finally:
                temporary.cleanup()
        drifted = copy.deepcopy(POLICY)
        drifted["performance_ratio_maximum"] = 1.20
        with self.assertRaises(RouteQualificationError):
            load_qualified_cached_route(
                entry_path=ROOT / "examples/modus_profile_router/long-horizon-p2b-v1/route-cache.json",
                current_key=key_from_config("p2b"),
                envelope_path=ROOT / "examples/modus_profile_router/long-horizon-p2b-v1/route-qualification.json",
                evidence_root=ROOT, current_policy=drifted,
            )

    def test_outcome_configs_match_bound_artifact_metrics(self):
        p2b = json.loads((ROOT / "agentic-artifacts/modus-codex-luna-max-long-horizon-p2b-transfer-v1.json").read_text())
        p2b_config = json.loads((ROOT / "configs/modus_p2b_route_qualification_v1.json").read_text())
        self.assertEqual(p2b_config["observed"]["performance_ratio"], p2b["performance"]["routed_final_ratio_to_fastest"])
        self.assertEqual(p2b_config["observed"]["maximum_relative_mad"], p2b["validity"]["maximum_relative_mad"])
        self.assertEqual(p2b_config["observed"]["token_saving_fraction"], p2b["deployment"]["e2e_saving_fraction"])
        p2d = json.loads((ROOT / "agentic-artifacts/modus-codex-luna-max-long-horizon-p2d-final-v1.json").read_text())
        p2d_config = json.loads((ROOT / "configs/modus_p2d_route_qualification_v1.json").read_text())
        self.assertEqual(p2d_config["observed"]["performance_ratio"], p2d["replicated_aggregates"]["routed_final_ratio_to_fastest"])
        self.assertEqual(p2d_config["observed"]["token_saving_fraction"], p2d["replicated_aggregates"]["worker_saving_fraction"])

    def test_mechanism_evidence_binds_qualified_and_rejected_envelopes(self):
        value = json.loads((ROOT / "agentic-artifacts/modus-route-qualification-envelope-v1.json").read_text())
        self.assertFalse(value["scientific_evidence"])
        self.assertTrue(value["model_free_mechanism_evidence"])
        self.assertEqual(value["positive_case"]["status"], "qualified")
        self.assertEqual(value["positive_case"]["deployment_router_model_calls"], 0)
        self.assertEqual(value["negative_case"]["status"], "rejected")
        self.assertFalse(value["negative_case"]["deployment_route_returned"])
        for file_key, hash_key in (("owner", "owner_sha256"), ("builder", "builder_sha256"), ("p2b_cache", "p2b_cache_sha256"), ("p2b_envelope", "p2b_envelope_sha256"), ("p2d_envelope", "p2d_envelope_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["files"][file_key]).read_bytes()).hexdigest(), value["files"][hash_key])


if __name__ == "__main__":
    unittest.main()

import copy
import hashlib
import json
from pathlib import Path
import unittest

from acrouter_repro.codex_spark_shadow import (
    SparkShadowError,
    _validate_profile_mechanism_contract,
    validate_profile_mechanism_response,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/modus_p2b_qualified_router_contract_v1.json"


def dispatch(stage, profile, mechanism, evidence):
    return {
        "stage": stage, "decision": "dispatch", "profile": profile,
        "mechanism_id": mechanism, "evidence_ref": evidence,
    }


class ModusEvidenceGatedAgentTest(unittest.TestCase):
    def load(self):
        return json.loads(CONFIG.read_text())

    def test_p2b_exact_qualified_route_is_allowed(self):
        contract = self.load()["response_contract"]
        _validate_profile_mechanism_contract(contract)
        response = {"schema": contract["schema"], "routes": [
            dispatch("stage-L", "p000", "local-prefix-sum-v1", "qualification:p2b:stage-L"),
            dispatch("stage-S", "e1v2", "shared-prefix-sum-v1", "qualification:p2b:stage-S"),
        ]}
        self.assertIsNone(validate_profile_mechanism_response(response, contract))

    def test_p2d_historical_reverse_route_is_rejected_before_workers(self):
        contract = self.load()["response_contract"]
        response = {"schema": contract["schema"], "routes": [
            dispatch("stage-L", "e1v2", "shared-prefix-sum-v1", "qualification:p2b:stage-S"),
            dispatch("stage-S", "p000", "local-prefix-sum-v1", "qualification:p2b:stage-L"),
        ]}
        self.assertEqual(
            validate_profile_mechanism_response(response, contract),
            "routes[0] is not outcome-qualified",
        )

    def test_missing_partial_or_swapped_evidence_is_rejected(self):
        contract = self.load()["response_contract"]
        base = {"schema": contract["schema"], "routes": [
            dispatch("stage-L", "p000", "local-prefix-sum-v1", "qualification:p2b:stage-L"),
            dispatch("stage-S", "e1v2", "shared-prefix-sum-v1", "qualification:p2b:stage-S"),
        ]}
        missing = copy.deepcopy(base)
        missing["routes"][0]["evidence_ref"] = None
        self.assertEqual(
            validate_profile_mechanism_response(missing, contract),
            "routes[0].evidence_ref is required for a mechanism",
        )
        swapped = copy.deepcopy(base)
        swapped["routes"][0]["evidence_ref"] = "qualification:p2b:stage-S"
        self.assertEqual(
            validate_profile_mechanism_response(swapped, contract),
            "routes[0] is not outcome-qualified",
        )

    def test_explicit_abstain_remains_valid(self):
        contract = self.load()["response_contract"]
        abstain = {
            "stage": "", "decision": "abstain", "profile": None,
            "mechanism_id": None, "evidence_ref": None,
        }
        response = {"schema": contract["schema"], "routes": []}
        for stage in contract["stages"]:
            response["routes"].append({**abstain, "stage": stage})
        self.assertIsNone(validate_profile_mechanism_response(response, contract))

    def test_contract_and_qualification_source_are_fail_closed(self):
        value = self.load()
        source = ROOT / value["qualification_source"]["path"]
        self.assertEqual(
            hashlib.sha256(source.read_bytes()).hexdigest(),
            value["qualification_source"]["sha256"],
        )
        envelope = json.loads(source.read_text())
        self.assertEqual(envelope["status"], "qualified")
        invalid = copy.deepcopy(value["response_contract"])
        invalid["qualified_routes"][0]["evidence_ref"] = "invented"
        with self.assertRaises(SparkShadowError):
            _validate_profile_mechanism_contract(invalid)

    def test_mechanism_evidence_binds_validator_contract_and_envelope(self):
        value = json.loads((ROOT / "agentic-artifacts/modus-evidence-gated-agent-v1.json").read_text())
        self.assertFalse(value["scientific_evidence"])
        self.assertTrue(value["model_free_mechanism_evidence"])
        self.assertEqual(value["positive_replay"]["validator_result"], "allow")
        self.assertEqual(value["negative_replay"]["validator_result"], "reject before Workers")
        self.assertTrue(value["fail_closed_checks"]["explicit_abstain_valid"])
        for file_key, hash_key in (("validator", "validator_sha256"), ("qualified_contract", "qualified_contract_sha256"), ("qualification_envelope", "qualification_envelope_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["files"][file_key]).read_bytes()).hexdigest(), value["files"][hash_key])


if __name__ == "__main__":
    unittest.main()

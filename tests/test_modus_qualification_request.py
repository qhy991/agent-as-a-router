import copy
import json
from pathlib import Path
import unittest

from acrouter_repro.modus_mechanism_registry import load_mechanism_registry, match_typed_mechanisms
from acrouter_repro.modus_qualification_request import resolve_qualification_request

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "examples/modus_profile_router/partial-lifecycle-p2f-v1/qualification-request.json"
VIEW = ROOT / "examples/modus_profile_router/partial-lifecycle-p2f-v1/p2g-candidate-view.json"
RESOLUTION = ROOT / "examples/modus_profile_router/partial-lifecycle-p2f-v1/p2g-resolution.json"

class ModusQualificationRequestTest(unittest.TestCase):
    def test_registry_v2_derives_exact_token_frequency_candidate(self):
        registry = load_mechanism_registry(ROOT / "configs/modus_mechanism_evidence_v2.json")
        matches = match_typed_mechanisms(registry, {
            "worker_model": "gpt-5.6-luna", "semantic_kind": "token_frequency",
            "reuse_batches": 120,
            "performance_objective": "latency_subject_to_correctness_then_tokens",
        })
        self.assertEqual(matches, [{
            "mechanism_id": "shared-token-frequency-v1",
            "profile": "e1v2",
            "evidence_ref": "qualification:p2c:stage-S",
        }])

    def test_actual_request_is_accepted_without_router_or_neutral_fallback(self):
        request = json.loads(REQUEST.read_text()); view = json.loads(VIEW.read_text())
        result = resolve_qualification_request(request, view)
        self.assertEqual(result, json.loads(RESOLUTION.read_text()))
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["neutral_fallbacks"], 0)
        self.assertEqual(result["worker_dispatch"]["profile"], "e1v2")

    def test_descriptor_mismatch_fails_and_empty_candidate_stays_pending(self):
        request = json.loads(REQUEST.read_text()); view = json.loads(VIEW.read_text())
        wrong = copy.deepcopy(view)
        wrong["stages"][0]["descriptor"]["semantic_kind"] = "other"
        with self.assertRaises(ValueError):
            resolve_qualification_request(request, wrong)
        pending = copy.deepcopy(view)
        pending["stages"][0]["resolution"] = {
            "decision": "abstain", "reason": "unqualified_task_state", "candidates": [],
        }
        result = resolve_qualification_request(request, pending)
        self.assertEqual(result["status"], "pending")
        self.assertIsNone(result["worker_dispatch"])

if __name__ == "__main__": unittest.main()

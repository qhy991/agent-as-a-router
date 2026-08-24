import copy
import hashlib
import json
from pathlib import Path
import unittest

from acrouter_repro.modus_dispatch_plan import DispatchPlanError, build_dispatch_plan
from acrouter_repro.modus_route_cache import sha256_value


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_p2e_autonomous_agent_v3.json"
VIEW = ROOT / "examples/modus_profile_router/evidence-gated-agent-v1/p2e-v2-candidate-view.json"
SCORE = ROOT / "examples/modus_profile_router/evidence-gated-agent-v1/p2e-v3-results/score.json"
PLAN = ROOT / "examples/modus_profile_router/evidence-gated-agent-v1/p2e-v3-results/dispatch-plan.json"


class ModusDispatchPlanTest(unittest.TestCase):
    def fixture(self):
        protocol = json.loads(PROTOCOL.read_text())
        view = json.loads(VIEW.read_text())
        response = json.loads(SCORE.read_text())["response"]
        return protocol["response_contract"], view, response

    def build(self, contract, view, response):
        return build_dispatch_plan(
            response=response, contract=contract, candidate_view=view,
            response_sha256=sha256_value(response),
            candidate_view_sha256=hashlib.sha256(VIEW.read_bytes()).hexdigest(),
        )

    def test_p2e_mixed_response_yields_one_dispatch_one_request_no_fallback(self):
        contract, view, response = self.fixture()
        plan = self.build(contract, view, response)
        self.assertEqual(plan["status"], "partial_pending_qualification")
        self.assertFalse(plan["complete"])
        self.assertEqual(plan["neutral_fallbacks"], 0)
        self.assertEqual(plan["worker_dispatches"], [{
            "stage": "stage-qualified", "profile": "e1v2",
            "mechanism_id": "shared-prefix-sum-v1",
            "evidence_ref": "qualification:p2b:stage-S",
        }])
        self.assertEqual(len(plan["qualification_requests"]), 1)
        self.assertEqual(plan["qualification_requests"][0]["stage"], "stage-unqualified")
        self.assertEqual(plan["qualification_requests"][0]["reason"], "unqualified_task_state")

    def test_all_abstain_defers_and_full_dispatch_completes(self):
        contract, view, response = self.fixture()
        abstain_view = copy.deepcopy(view)
        abstain_response = copy.deepcopy(response)
        for row, route in zip(abstain_view["stages"], abstain_response["routes"], strict=True):
            row["resolution"] = {"decision": "abstain", "reason": "unqualified_task_state", "candidates": []}
            route.update({"decision": "abstain", "profile": None, "mechanism_id": None, "evidence_ref": None})
        plan = self.build(contract, abstain_view, abstain_response)
        self.assertEqual(plan["status"], "deferred_pending_qualification")
        self.assertEqual(len(plan["worker_dispatches"]), 0)
        self.assertEqual(len(plan["qualification_requests"]), 2)

        full_view = copy.deepcopy(view)
        full_response = copy.deepcopy(response)
        first_action = full_view["stages"][0]["resolution"]["action"]
        full_view["stages"][1]["resolution"] = {
            "decision": "dispatch", "reason": "single_typed_candidate",
            "action": first_action,
        }
        full_response["routes"][1].update({
            "decision": "dispatch", "profile": first_action["profile"],
            "mechanism_id": first_action["mechanism_id"],
            "evidence_ref": first_action["evidence_ref"],
        })
        full_contract = copy.deepcopy(contract)
        full_contract["qualified_routes"].append({
            "stage": "stage-unqualified", **first_action,
        })
        plan = self.build(full_contract, full_view, full_response)
        self.assertEqual(plan["status"], "complete")
        self.assertTrue(plan["complete"])
        self.assertEqual(len(plan["worker_dispatches"]), 2)
        self.assertEqual(len(plan["qualification_requests"]), 0)

    def test_response_view_stage_action_and_neutral_fallback_mismatches_fail(self):
        contract, view, response = self.fixture()
        mutations = []
        swapped = copy.deepcopy(response)
        swapped["routes"].reverse()
        mutations.append((view, swapped))
        wrong_action_view = copy.deepcopy(view)
        wrong_action_view["stages"][0]["resolution"]["action"]["profile"] = "p000"
        mutations.append((wrong_action_view, response))
        missing_view = copy.deepcopy(view)
        missing_view["stages"].pop()
        mutations.append((missing_view, response))
        neutral = copy.deepcopy(response)
        neutral["routes"][1].update({
            "decision": "dispatch", "profile": "neutral",
            "mechanism_id": None, "evidence_ref": None,
        })
        mutations.append((view, neutral))
        for index, (candidate_view, candidate_response) in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(DispatchPlanError):
                self.build(contract, candidate_view, candidate_response)

    def test_checked_in_plan_is_hash_bound_partial_state(self):
        value = json.loads(PLAN.read_text())
        self.assertEqual(value["status"], "partial_pending_qualification")
        self.assertFalse(value["complete"])
        self.assertEqual(value["neutral_fallbacks"], 0)
        self.assertEqual(value["source"]["candidate_view_sha256"], hashlib.sha256(VIEW.read_bytes()).hexdigest())

    def test_manager_mechanism_evidence_binds_actual_partial_plan(self):
        value = json.loads((ROOT / "agentic-artifacts/modus-manager-partial-dispatch-plan-v1.json").read_text())
        self.assertTrue(value["model_free_manager_mechanism_evidence"])
        self.assertEqual(value["actual_plan"]["status"], "partial_pending_qualification")
        self.assertFalse(value["actual_plan"]["complete"])
        self.assertEqual(value["actual_plan"]["neutral_fallbacks"], 0)
        self.assertEqual(len(value["actual_plan"]["worker_dispatches"]), 1)
        self.assertEqual(len(value["actual_plan"]["qualification_requests"]), 1)
        for file_key, hash_key in (("owner", "owner_sha256"), ("builder", "builder_sha256"), ("candidate_view", "candidate_view_sha256"), ("agent_score", "agent_score_sha256"), ("dispatch_plan", "dispatch_plan_sha256")):
            self.assertEqual(hashlib.sha256((ROOT / value["files"][file_key]).read_bytes()).hexdigest(), value["files"][hash_key])


if __name__ == "__main__":
    unittest.main()

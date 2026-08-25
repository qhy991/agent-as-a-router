import hashlib
import json
from pathlib import Path
import unittest

from scripts.run_modus_profile_experience_transfer import derive_cells
from scripts.score_modus_profile_experience_router import parse_response


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_profile_experience_transfer.json"
LEGACY_TERMS = ("p2s", "p2t", "p000", "p100", "e1v2", "e1v3")


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


class ModusProfileExperienceTransferTest(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads(PROTOCOL.read_text())

    def test_agent_visible_policy_context_and_prompt_are_formal(self):
        for relative in (
            self.protocol["router"]["policy"],
            self.protocol["router"]["context"],
            self.protocol["router"]["prompt"],
        ):
            text = (ROOT / relative).read_text().lower()
            self.assertFalse(
                any(term in text for term in LEGACY_TERMS),
                f"historical codename leaked through {relative}",
            )
        self.assertEqual(
            set(self.protocol["strategies"]),
            {
                "unconstrained-optimization",
                "target-scoped-optimization",
                "prepared-shared-optimization",
            },
        )
        self.assertFalse(
            self.protocol["provenance"]["historical_codenames_agent_visible"]
        )

    def test_protocol_is_frozen_staged_and_economic(self):
        value = self.protocol
        self.assertTrue(value["run_authorized"])
        self.assertFalse(value["router"]["worker_outcomes_available"])
        self.assertEqual(value["router"]["calls"], 1)
        self.assertEqual(value["execution"]["authorized_worker_range"], [3, 6])
        self.assertTrue(value["execution"]["no_followup_replication"])
        self.assertTrue(value["execution"]["no_counterfactual_matrix_completion"])
        self.assertEqual(
            value["execution"]["fixed_baseline_strategy"],
            "prepared-shared-optimization",
        )
        self.assertEqual(value["expected_future_deployments"], 8)
        self.assertEqual(value["economics"]["prior_experience_acquisition_tokens"], 2952770)

    def test_every_source_is_hash_bound(self):
        value = self.protocol
        registry = json.loads(
            (ROOT / value["router"]["experience_registry"]).read_text()
        )
        registered = {
            row["strategy_id"]: row["artifact_sha256"]
            for row in registry["strategies"]
        }
        for strategy_id, strategy in value["strategies"].items():
            self.assertEqual(
                strategy["artifact_sha256"], registered[strategy_id]
            )
            if strategy["artifact_path"] is not None:
                self.assertFalse(Path(strategy["artifact_path"]).is_absolute())
        self.assertNotIn("/Users/", PROTOCOL.read_text())
        for section, path_key, hash_key in (
            ("router", "policy", "policy_sha256"),
            ("router", "experience_registry", "experience_registry_sha256"),
            ("router", "context_builder", "context_builder_sha256"),
            ("router", "context", "context_sha256"),
            ("router", "prompt", "prompt_sha256"),
            ("router", "scorer", "scorer_sha256"),
            ("qualification", "path", "sha256"),
            ("execution", "runner", "runner_sha256"),
            ("execution", "verifier", "verifier_sha256"),
            ("execution", "custody_wrapper", "custody_wrapper_sha256"),
            ("execution", "custody_qualification", "custody_qualification_sha256"),
            ("scoring", "scorer", "scorer_sha256"),
        ):
            path = ROOT / value[section][path_key]
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                value[section][hash_key],
            )
        for task in value["tasks"].values():
            self.assertEqual(
                tree_sha256(ROOT / task["seed_root"]),
                task["seed_tree_sha256"],
            )
            self.assertEqual(
                hashlib.sha256((ROOT / task["prompt"]).read_bytes()).hexdigest(),
                task["prompt_sha256"],
            )

    def _response(self):
        routes = []
        for task_id in self.protocol["router"]["tasks"]:
            qualified = self.protocol["router"]["qualified_dispatch"][task_id]
            routes.append({
                "task_id": task_id,
                "decision": "dispatch",
                "strategy": qualified["strategy"],
                "evidence_refs": [qualified["evidence_ref"]],
                "reason": "matched accumulated qualified experience",
            })
        return {"schema": "modus-router-batch-decision-v1", "routes": routes}

    def test_router_parser_and_staged_cell_derivation(self):
        parsed = parse_response(json.dumps(self._response()), self.protocol)
        router_score = {
            "status": "pass",
            "worker_acquisition_authorized": True,
            "parsed": parsed,
        }
        cells = derive_cells(self.protocol, router_score)
        self.assertEqual(len(cells), 5)
        self.assertEqual(
            [(cell["task_id"], cell["strategy"], cell["role"]) for cell in cells],
            [
                ("single-batch-keyed-reduction", "prepared-shared-optimization", "fixed-reference"),
                ("single-batch-keyed-reduction", "target-scoped-optimization", "router-selected"),
                ("repeated-batch-keyed-aggregate", "prepared-shared-optimization", "fixed-reference"),
                ("direct-bit-transformation", "prepared-shared-optimization", "fixed-reference"),
                ("direct-bit-transformation", "target-scoped-optimization", "router-selected"),
            ],
        )

    def test_router_cannot_swap_evidence_or_invent_strategy(self):
        response = self._response()
        response["routes"][0]["evidence_refs"] = [
            self.protocol["router"]["qualified_dispatch"][
                "repeated-batch-keyed-aggregate"
            ]["evidence_ref"]
        ]
        with self.assertRaisesRegex(ValueError, "dispatch evidence differs"):
            parse_response(json.dumps(response), self.protocol)
        response = self._response()
        response["routes"][0]["strategy"] = "unconstrained-optimization"
        with self.assertRaisesRegex(ValueError, "dispatch strategy is not qualified"):
            parse_response(json.dumps(response), self.protocol)


if __name__ == "__main__":
    unittest.main()

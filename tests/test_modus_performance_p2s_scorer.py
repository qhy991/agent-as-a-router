import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import score_modus_performance_p2s_matrix as scorer


TASKS = ("keyed-closest-negative", "keyed-distinct-quartic-sum", "rotate-mix32")
PROFILES = ("neutral", "p000v2", "e1v3")


class P2sMatrixScorerTest(unittest.TestCase):
    def _run(self, agent_actions):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_root = root / "run"
            cells = []
            seconds = {
                ("keyed-closest-negative", "neutral"): 1.0,
                ("keyed-closest-negative", "p000v2"): 1.0,
                ("keyed-closest-negative", "e1v3"): 1.3,
                ("keyed-distinct-quartic-sum", "neutral"): 1.0,
                ("keyed-distinct-quartic-sum", "p000v2"): 1.3,
                ("keyed-distinct-quartic-sum", "e1v3"): 1.0,
                ("rotate-mix32", "neutral"): 1.0,
                ("rotate-mix32", "p000v2"): 1.3,
                ("rotate-mix32", "e1v3"): 1.3,
            }
            tokens = {
                ("keyed-closest-negative", "neutral"): 100,
                ("keyed-closest-negative", "p000v2"): 50,
                ("keyed-closest-negative", "e1v3"): 70,
                ("keyed-distinct-quartic-sum", "neutral"): 100,
                ("keyed-distinct-quartic-sum", "p000v2"): 70,
                ("keyed-distinct-quartic-sum", "e1v3"): 50,
                ("rotate-mix32", "neutral"): 100,
                ("rotate-mix32", "p000v2"): 80,
                ("rotate-mix32", "e1v3"): 90,
            }
            token_by_cell = {}
            order = 1
            for task in TASKS:
                for profile in PROFILES:
                    cell = {"id": f"{task}-{profile}", "task": task, "profile": profile, "order": order}
                    order += 1
                    cells.append(cell)
                    cell_root = run_root / "cells" / cell["id"]
                    cell_root.mkdir(parents=True)
                    verification = {
                        "passed": True,
                        "implementation_digest": cell["id"],
                        "benchmark": {"steady_seconds": seconds[(task, profile)], "steady_relative_mad": 0.01},
                    }
                    (cell_root / "verification.json").write_text(json.dumps(verification))
                    token_by_cell[cell["id"]] = tokens[(task, profile)]
            protocol = {
                "cells": cells,
                "tasks": {
                    "keyed-closest-negative": {"expected_preference": "p000v2"},
                    "keyed-distinct-quartic-sum": {"expected_preference": "e1v3"},
                    "rotate-mix32": {"expected_preference": "neutral"},
                },
            }
            protocol_path = root / "configs" / "protocol.json"
            protocol_path.parent.mkdir()
            protocol_path.write_text(json.dumps(protocol))
            router = {"status": "pass", "parsed": {"actions_by_task": agent_actions}, "router_tokens": 10}
            router_path = root / "router.json"
            router_path.write_text(json.dumps(router))
            output = root / "score.json"
            def usage(path):
                return True, token_by_cell[path.parents[1].name]
            with mock.patch.object(scorer, "_wave_usage", side_effect=usage):
                rc = scorer.main(["--run-root", str(run_root), "--protocol", str(protocol_path), "--router-score", str(router_path), "--output", str(output)])
            return rc, json.loads(output.read_text())

    def test_uses_best_eligible_fixed_baseline_and_exact_oracle(self):
        agent = {
            "keyed-closest-negative": "p000v2",
            "keyed-distinct-quartic-sum": "e1v3",
            "rotate-mix32": "neutral",
        }
        rc, value = self._run(agent)
        self.assertEqual(rc, 0)
        self.assertEqual(value["oracle_route"], agent)
        self.assertEqual(value["deployment"]["best_eligible_fixed_profile"], "neutral")
        self.assertAlmostEqual(value["deployment"]["saving_fraction_vs_best_eligible_fixed"], 1 / 3)
        self.assertEqual(value["agent_match_count"], 3)

    def test_agent_mismatch_cannot_promote(self):
        rc, value = self._run({task: "neutral" for task in TASKS})
        self.assertEqual(rc, 0)
        self.assertEqual(value["agent_match_count"], 1)
        self.assertEqual(value["decision"], "stop_or_continue_evidence")
        self.assertEqual(value["economics"]["decision"], "defer_correctness")


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import score_modus_profile_experience_transfer as scorer


class ModusProfileExperienceTransferScorerTest(unittest.TestCase):
    def test_marginal_and_full_lineage_economics_remain_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_root = root / "run"
            routes = {
                "single-batch-keyed-reduction": "target-scoped-optimization",
                "repeated-batch-keyed-aggregate": "prepared-shared-optimization",
                "direct-bit-transformation": "target-scoped-optimization",
            }
            cells = []
            tokens = {}
            for task_id, selected in routes.items():
                reference_id = f"{task_id}--reference"
                cells.append({
                    "id": reference_id,
                    "task_id": task_id,
                    "strategy": "prepared-shared-optimization",
                    "role": "fixed-reference",
                    "order": len(cells) + 1,
                    "status": "pass",
                })
                tokens[reference_id] = 200
                if selected != "prepared-shared-optimization":
                    selected_id = f"{task_id}--selected"
                    cells.append({
                        "id": selected_id,
                        "task_id": task_id,
                        "strategy": selected,
                        "role": "router-selected",
                        "order": len(cells) + 1,
                        "status": "pass",
                    })
                    tokens[selected_id] = 100
            for cell in cells:
                cell_root = run_root / "cells" / cell["id"]
                cell_root.mkdir(parents=True)
                (cell_root / "verification.json").write_text(json.dumps({
                    "passed": True,
                    "implementation_digest": cell["id"],
                    "benchmark": {
                        "steady_seconds": 1.0,
                        "steady_relative_mad": 0.01,
                    },
                }))
            (run_root / "execution-summary.json").write_text(json.dumps({
                "status": "pass",
                "cells": cells,
            }))
            protocol = {
                "router": {"tasks": list(routes)},
                "tasks": {
                    task_id: {"expected_transfer_strategy": strategy}
                    for task_id, strategy in routes.items()
                },
                "execution": {
                    "fixed_baseline_strategy": "prepared-shared-optimization"
                },
                "scoring": {
                    "maximum_performance_ratio": 1.25,
                    "maximum_relative_mad": 0.10,
                    "minimum_token_saving_fraction": 0.15,
                },
                "economics": {
                    "prior_experience_acquisition_tokens": 2_952_770
                },
                "expected_future_deployments": 8,
            }
            protocol_path = root / "configs" / "protocol.json"
            protocol_path.parent.mkdir()
            protocol_path.write_text(json.dumps(protocol))
            router_score = {
                "router_tokens": 10,
                "parsed": {
                    "routes": [
                        {
                            "task_id": task_id,
                            "decision": "dispatch",
                            "strategy": strategy,
                        }
                        for task_id, strategy in routes.items()
                    ]
                },
            }
            router_path = root / "router-score.json"
            router_path.write_text(json.dumps(router_score))
            output = root / "score.json"

            def usage(path):
                return True, tokens[path.parents[1].name]

            with mock.patch.object(scorer, "_wave_usage", side_effect=usage):
                result = scorer.main([
                    "--run-root", str(run_root),
                    "--protocol", str(protocol_path),
                    "--router-score", str(router_path),
                    "--output", str(output),
                ])
            self.assertEqual(result, 0)
            value = json.loads(output.read_text())
            self.assertEqual(value["transfer_prediction_match_count"], 3)
            self.assertTrue(value["quality_passed"])
            self.assertAlmostEqual(value["deployment"]["saving_fraction"], 1 / 3)
            self.assertEqual(value["acquisition"]["worker_cells"], 5)
            self.assertEqual(value["marginal_economics"]["decision"], "promote")
            self.assertEqual(value["decision"], "pass_economic")
            self.assertLess(
                value["full_lineage_economics"]["net_tokens_at_expected_deployments"],
                0,
            )


if __name__ == "__main__":
    unittest.main()

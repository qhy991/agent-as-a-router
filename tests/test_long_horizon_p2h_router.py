import json
from pathlib import Path
import tempfile
import unittest

from scripts.score_modus_long_horizon_p2h_router import _parse_decision, main


class LongHorizonP2hRouterTest(unittest.TestCase):
    def test_exact_two_stage_proposal_parses(self):
        value = _parse_decision(
            json.dumps({
                "schema": "modus-long-horizon-p2h-router-decision-v1",
                "routes": [
                    {"stage": "stage-L", "action": "p000", "reason": "local"},
                    {"stage": "stage-S", "action": "e1v2", "reason": "reuse"},
                ],
            }),
            ["stage-L", "stage-S"],
            ["neutral", "p000", "e1v2"],
        )
        self.assertEqual(value["actions_by_stage"], {"stage-L": "p000", "stage-S": "e1v2"})

    def test_valid_proposal_never_authorizes_worker_deployment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "output/router").mkdir(parents=True)
            (root / "output/router/last-message.txt").write_text(json.dumps({
                "schema": "modus-long-horizon-p2h-router-decision-v1",
                "routes": [
                    {"stage": "stage-L", "action": "p000", "reason": "local"},
                    {"stage": "stage-S", "action": "e1v2", "reason": "reuse"},
                ],
            }))
            (root / "output/wave-result.json").write_text(json.dumps({
                "status": "pass",
                "cells": [{
                    "cell": "router", "valid_execution": True,
                    "usage": {"input_tokens": 10, "output_tokens": 5},
                }],
            }))
            protocol = root / "protocol.json"
            protocol.write_text(json.dumps({"router": {
                "stages": ["stage-L", "stage-S"],
                "allowed_actions": ["neutral", "p000", "e1v2"],
                "repetitions": 1,
            }}))
            output = root / "score.json"
            self.assertEqual(main([
                "--run-root", str(root), "--protocol", str(protocol),
                "--output", str(output),
            ]), 0)
            result = json.loads(output.read_text())
            self.assertTrue(result["qualification_pair_protocol_authorized"])
            self.assertFalse(result["worker_deployment_authorized"])


if __name__ == "__main__":
    unittest.main()

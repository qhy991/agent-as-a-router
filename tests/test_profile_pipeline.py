import copy
import json
from pathlib import Path
import tempfile
import unittest

from acrouter_repro.profile_pipeline import (
    ProfileReplayContractError,
    analyze_profile_file,
    analyze_profile_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/modus_profile_replay.json"
CELLS = ROOT / "examples/modus_profile_router/modus-fixed-behavior-pilot-v2-cells.json"


class ProfilePipelineTest(unittest.TestCase):
    def test_modus_replay_reports_no_routing_space(self):
        result = analyze_profile_file(CONFIG, CELLS)
        self.assertEqual(result["claim_status"], "no-profile-routing-space-observed")
        self.assertEqual(result["best_fixed_profile"]["profile"], "p000")
        self.assertEqual(
            result["oracle"]["actions_by_task"],
            {
                "degree-h01-perf-p1c": "p000",
                "timeslice-h01-perf-p1c": "p000",
            },
        )
        self.assertEqual(result["oracle"]["saving_fraction_vs_best_fixed"], 0.0)
        self.assertFalse(result["routing_space"]["observed"])
        degree_p100 = result["tasks"]["degree-h01-perf-p1c"]["actions"]["p100"]
        self.assertEqual(degree_p100["behavior_fidelity_fraction"], 2 / 3)
        self.assertFalse(degree_p100["behavior_fidelity_passed"])

    def test_file_replay_writes_machine_and_human_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = analyze_profile_file(CONFIG, CELLS, Path(temporary))
            self.assertTrue((Path(temporary) / "profile_replay.json").is_file())
            self.assertTrue((Path(temporary) / "summary.md").is_file())
            self.assertEqual(
                json.loads((Path(temporary) / "profile_replay.json").read_text()),
                result,
            )

    def test_missing_fixed_cell_fails_closed(self):
        config = json.loads(CONFIG.read_text())
        payload = json.loads(CELLS.read_text())
        with self.assertRaises(ProfileReplayContractError):
            analyze_profile_matrix(config, payload["cells"][:-1])

    def test_even_repetition_token_median_is_not_truncated(self):
        config = json.loads(CONFIG.read_text())
        config["repetitions"] = 2
        payload = json.loads(CELLS.read_text())
        cells = [row for row in payload["cells"] if row["repetition"] <= 2]
        result = analyze_profile_matrix(config, cells)
        self.assertEqual(
            result["tasks"]["degree-h01-perf-p1c"]["actions"]["p000"]["median_total_tokens"],
            75718.5,
        )

    def test_source_hash_drift_fails_closed(self):
        config = json.loads(CONFIG.read_text())
        config["source"]["cells_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            config_path = Path(temporary) / "config.json"
            config_path.write_text(json.dumps(config))
            with self.assertRaises(ProfileReplayContractError):
                analyze_profile_file(config_path, CELLS)

    def test_non_positive_or_non_finite_performance_fails_closed(self):
        config = json.loads(CONFIG.read_text())
        payload = json.loads(CELLS.read_text())
        for value in (0.0, float("inf"), float("nan")):
            with self.subTest(value=value):
                cells = copy.deepcopy(payload["cells"])
                cells[0]["steady_seconds"] = value
                with self.assertRaises(ProfileReplayContractError):
                    analyze_profile_matrix(config, cells)

    def test_synthetic_crossover_exposes_routing_space(self):
        config = {
            "name": "synthetic-crossover",
            "tasks": ["local", "system"],
            "actions": ["neutral", "p000", "p100"],
            "action_tie_order": ["neutral", "p000", "p100"],
            "repetitions": 1,
            "profiles": {
                "neutral": {"required_topology": None},
                "p000": {"required_topology": "local"},
                "p100": {"required_topology": "coordinated"},
            },
            "performance": {
                "metric": "steady_seconds",
                "lower_is_better": True,
                "eligible_ratio_over_fastest": 0.25,
            },
            "minimum_oracle_saving_fraction": 0.15,
        }
        token_table = {
            "local": {"neutral": 100, "p000": 50, "p100": 200},
            "system": {"neutral": 100, "p000": 200, "p100": 50},
        }
        topology = {"neutral": "other", "p000": "local", "p100": "coordinated"}
        cells = []
        for task in config["tasks"]:
            for action in config["actions"]:
                total = token_table[task][action]
                cells.append({
                    "cell_id": f"{task}-{action}",
                    "task": task,
                    "action": action,
                    "repetition": 1,
                    "terminal": "completed",
                    "correct": True,
                    "topology": topology[action],
                    "steady_seconds": 1.0,
                    "new_tokens": total,
                    "cache_read_tokens": 0,
                    "total_tokens": total,
                })
        result = analyze_profile_matrix(config, cells)
        self.assertEqual(result["best_fixed_profile"]["profile"], "neutral")
        self.assertEqual(result["oracle"]["actions_by_task"], {"local": "p000", "system": "p100"})
        self.assertEqual(result["oracle"]["saving_fraction_vs_best_fixed"], 0.5)
        self.assertTrue(result["routing_space"]["observed"])


if __name__ == "__main__":
    unittest.main()

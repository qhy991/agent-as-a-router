import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/modus_codex_spark_t_axis_v1.json"


class SparkTAxisTaskTest(unittest.TestCase):
    def test_matrix_changes_only_t_and_uses_two_waves(self):
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["profiles"]["p000"]["bits"], "E0/T0/A0")
        self.assertEqual(value["profiles"]["p010"]["bits"], "E0/T1/A0")
        self.assertEqual(len(value["dispatch"]["wave_1"]), 4)
        self.assertEqual(len(value["dispatch"]["wave_2"]), 4)
        self.assertFalse(value["dispatch"]["automatic_redispatch"])
        self.assertTrue(value["failure_policy"]["no_model_substitution"])

    def test_task_prompts_are_bound_and_forbid_external_information(self):
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
        for task in value["tasks"].values():
            path = ROOT / task["prompt"]
            text = path.read_text(encoding="utf-8")
            normalized = " ".join(text.split())
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), task["prompt_sha256"])
            self.assertIn(task["allowed_file"], text)
            self.assertIn("Do not use web search", normalized)
            self.assertIn("Do not modify tests", text)


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/modus_swe_a_axis_v1.json"


class AAxisTaskTest(unittest.TestCase):
    def test_task_is_single_axis_visible_feedback_and_not_authorized(self):
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(value["schema"], "acrouter-modus-swe-a-axis-task-v1")
        self.assertFalse(value["run_authorized"])
        self.assertEqual(value["single_axis_contract"]["changed_axis"], "A")
        self.assertEqual(
            value["single_axis_contract"]["unchanged_segments"],
            ["envelope", "E0", "T0"],
        )
        self.assertEqual(value["treatments"]["p000"]["bits"], "E0/T0/A0")
        self.assertEqual(value["treatments"]["p001"]["bits"], "E0/T0/A1")
        self.assertEqual(value["qualification"]["baseline_status"], "fail-as-required")
        self.assertEqual(value["qualification"]["gold_status"], "pass")
        self.assertTrue(value["qualification"]["visible_feedback_informative"])
        self.assertEqual(value["planned_matrix"]["root_cells"], 4)

    def test_prompt_is_bound_and_forbids_test_or_dependency_changes(self):
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
        prompt = ROOT / value["task"]["prompt"]
        text = prompt.read_text(encoding="utf-8")
        self.assertEqual(
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
            value["task"]["prompt_sha256"],
        )
        self.assertIn("django/db/models/deletion.py", text)
        self.assertIn("test_only_referenced_fields_selected", text)
        self.assertIn("Do not modify tests", text)
        self.assertIn("dependencies", text)


if __name__ == "__main__":
    unittest.main()

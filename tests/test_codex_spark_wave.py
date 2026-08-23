import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest

from acrouter_repro.codex_spark_wave import SparkWaveError, run_wave


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CodexSparkWaveTest(unittest.TestCase):
    def fixture(self, root: Path, *, web: bool = False) -> tuple[Path, Path, Path]:
        profile = root / "profile.md"
        task = root / "task.md"
        profile.write_text("profile\n", encoding="utf-8")
        task.write_text("task\n", encoding="utf-8")
        environment_bin = root / "env" / "bin"
        environment_bin.mkdir(parents=True)
        (environment_bin / "python").write_text("fixture\n", encoding="utf-8")
        fake = root / "fake-codex"
        item = (
            '{"type":"item.completed","item":{"type":"web_search"}}\n'
            if web else ""
        )
        fake.write_text(
            "#!/bin/sh\n"
            "cat >/dev/null\n"
            "printf '%s' '" + item + "'\n"
            "printf '%s\\n' '{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":10,\"cached_input_tokens\":2,\"cache_write_input_tokens\":0,\"output_tokens\":3,\"reasoning_output_tokens\":1}}'\n",
            encoding="utf-8",
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        cells = []
        for name in ("a", "b"):
            workspace = root / f"workspace-{name}"
            workspace.mkdir()
            cells.append({
                "cell": name,
                "workspace": str(workspace),
                "profile": str(profile),
                "profile_sha256": digest(profile),
                "task": str(task),
                "task_sha256": digest(task),
                "environment_bin": str(environment_bin),
            })
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({
            "schema": "acrouter-codex-spark-wave-v1",
            "model": "gpt-5.3-codex-spark",
            "reasoning_effort": "high",
            "timeout_seconds": 10,
            "automatic_redispatch": False,
            "cells": cells,
        }), encoding="utf-8")
        return manifest, fake, root / "output"

    def test_two_cells_run_once_with_complete_usage(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary))
            result = run_wave(manifest, output, codex=str(fake))
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["valid_execution_cells"], 2)
            self.assertEqual(result["automatic_redispatches"], 0)
            self.assertTrue(all(cell["usage_complete"] for cell in result["cells"]))
            expected_prompt = hashlib.sha256(
                b"profile\n\n\n--- Task ---\n\ntask\n"
            ).hexdigest()
            self.assertTrue(all(
                cell["prompt_sha256"] == expected_prompt for cell in result["cells"]
            ))

    def test_sol_model_is_an_explicit_supported_route(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary))
            value = json.loads(manifest.read_text())
            value["model"] = "gpt-5.6-sol"
            manifest.write_text(json.dumps(value))
            result = run_wave(manifest, output, codex=str(fake))
            self.assertEqual(result["status"], "pass")

    def test_luna_max_is_an_explicit_supported_route(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary))
            value = json.loads(manifest.read_text())
            value["model"] = "gpt-5.6-luna"
            value["reasoning_effort"] = "max"
            manifest.write_text(json.dumps(value))
            result = run_wave(manifest, output, codex=str(fake))
            self.assertEqual(result["status"], "pass")

    def test_max_effort_is_not_enabled_for_spark(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary))
            value = json.loads(manifest.read_text())
            value["reasoning_effort"] = "max"
            manifest.write_text(json.dumps(value))
            with self.assertRaisesRegex(SparkWaveError, "reasoning effort"):
                run_wave(manifest, output, codex=str(fake))

    def test_web_search_invalidates_wave_without_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary), web=True)
            result = run_wave(manifest, output, codex=str(fake))
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["valid_execution_cells"], 0)
            self.assertEqual(result["automatic_redispatches"], 0)

    def test_existing_output_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary))
            output.mkdir()
            with self.assertRaisesRegex(SparkWaveError, "already exists"):
                run_wave(manifest, output, codex=str(fake))


if __name__ == "__main__":
    unittest.main()

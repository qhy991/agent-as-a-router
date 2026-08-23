import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest

from acrouter_repro.codex_spark_shadow import (
    SparkShadowError,
    run_shadow,
    validate_profile_mechanism_response,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CodexSparkShadowTest(unittest.TestCase):
    def fixture(self, root: Path, *, extra_file: bool = False):
        system = root / "system.md"
        system.write_text("system contract\n", encoding="utf-8")
        fake = root / "fake-codex"
        fake.write_text(
            "#!/bin/sh\ncat >/dev/null\nmkdir -p outbox\n"
            "printf '%s\\n' '{\"schema\":\"fixture\"}' > outbox/route-response.json\n"
            + ("printf x > extra.txt\n" if extra_file else "")
            + "printf '%s\\n' '{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":10,\"cached_input_tokens\":2,\"cache_write_input_tokens\":0,\"output_tokens\":3,\"reasoning_output_tokens\":1}}'\n",
            encoding="utf-8",
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        cells = []
        for name in ("a", "b"):
            workspace = root / f"workspace-{name}"
            (workspace / "inbox").mkdir(parents=True)
            (workspace / "outbox").mkdir()
            task = workspace / "inbox" / "task.md"
            task.write_text(f"task {name}\n", encoding="utf-8")
            cells.append({"cell": name, "workspace": str(workspace), "task_sha256": digest(task)})
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({
            "schema": "acrouter-codex-shadow-v1",
            "model": "gpt-5.3-codex-spark",
            "reasoning_effort": "high",
            "timeout_seconds": 10,
            "automatic_redispatch": False,
            "system_prompt": str(system),
            "system_prompt_sha256": digest(system),
            "cells": cells,
        }), encoding="utf-8")
        return manifest, fake, root / "output"

    def test_sol_model_is_an_explicit_supported_route(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary))
            value = json.loads(manifest.read_text())
            value["model"] = "gpt-5.6-sol"
            manifest.write_text(json.dumps(value))
            result = run_shadow(manifest, output, codex=str(fake))
            self.assertEqual(result["status"], "pass")

    def test_luna_max_is_an_explicit_supported_route(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary))
            value = json.loads(manifest.read_text())
            value["model"] = "gpt-5.6-luna"
            value["reasoning_effort"] = "max"
            manifest.write_text(json.dumps(value))
            result = run_shadow(manifest, output, codex=str(fake))
            self.assertEqual(result["status"], "pass")

    def test_max_effort_is_not_enabled_for_spark(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary))
            value = json.loads(manifest.read_text())
            value["reasoning_effort"] = "max"
            manifest.write_text(json.dumps(value))
            with self.assertRaisesRegex(SparkShadowError, "reasoning effort"):
                run_shadow(manifest, output, codex=str(fake))

    def test_valid_shadow_preserves_exact_workspace_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary))
            result = run_shadow(manifest, output, codex=str(fake))
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["valid_execution_cells"], 2)
            self.assertTrue(all(cell["custody_passed"] for cell in result["cells"]))
            self.assertTrue(all(cell["response"] == {"schema": "fixture"} for cell in result["cells"]))

    def test_extra_workspace_file_invalidates_without_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary), extra_file=True)
            result = run_shadow(manifest, output, codex=str(fake))
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["automatic_redispatches"], 0)
            self.assertEqual(result["valid_execution_cells"], 0)

    def test_dirty_initial_workspace_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest, fake, output = self.fixture(Path(temporary))
            (Path(temporary) / "workspace-a" / "extra.txt").write_text("x")
            with self.assertRaisesRegex(SparkShadowError, "initial files differ"):
                run_shadow(manifest, output, codex=str(fake))

    def test_profile_mechanism_response_supports_dispatch_and_abstain(self):
        contract = {
            "schema": "modus-profile-mechanism-route-v1",
            "stages": ["known", "unknown"],
            "allowed_profiles": ["neutral", "p000", "p100"],
            "allowed_mechanism_ids": ["shared-prefix-sum-v1"],
            "require_evidence_ref_for_mechanism": True,
        }
        response = {
            "schema": "modus-profile-mechanism-route-v1",
            "routes": [
                {
                    "stage": "known",
                    "decision": "dispatch",
                    "profile": "p100",
                    "mechanism_id": "shared-prefix-sum-v1",
                    "evidence_ref": "case:rankcount-system",
                },
                {
                    "stage": "unknown",
                    "decision": "abstain",
                    "profile": None,
                    "mechanism_id": None,
                    "evidence_ref": None,
                },
            ],
        }
        self.assertIsNone(validate_profile_mechanism_response(response, contract))

    def test_profile_mechanism_response_fails_closed_without_evidence(self):
        contract = {
            "schema": "modus-profile-mechanism-route-v1",
            "stages": ["stage"],
            "allowed_profiles": ["neutral", "p000", "p100"],
            "allowed_mechanism_ids": ["shared-prefix-sum-v1"],
            "require_evidence_ref_for_mechanism": True,
        }
        response = {
            "schema": "modus-profile-mechanism-route-v1",
            "routes": [{
                "stage": "stage",
                "decision": "dispatch",
                "profile": "p100",
                "mechanism_id": "shared-prefix-sum-v1",
                "evidence_ref": None,
            }],
        }
        self.assertEqual(
            validate_profile_mechanism_response(response, contract),
            "routes[0].evidence_ref is required for a mechanism",
        )


if __name__ == "__main__":
    unittest.main()

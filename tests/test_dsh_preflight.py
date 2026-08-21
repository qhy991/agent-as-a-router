import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from acrouter_repro.dsh_preflight import REQUIRED_CONTRACT, run_dsh_preflight


class DshPreflightTest(unittest.TestCase):
    def setUp(self):
        if shutil.which("git") is None or shutil.which("pnpm") is None:
            self.skipTest("git and pnpm are required")

    def _repository(self, root: Path, files: dict[str, str]) -> str:
        root.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            [
                "git", "-c", "user.name=Fixture", "-c",
                "user.email=fixture@example.invalid", "commit", "-qm", "fixture",
            ],
            cwd=root,
            check=True,
        )
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def _fixture(self, *, include_contract: bool = True):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        dsh = root / "dsh"
        dsh_commit = self._repository(dsh, {"pnpm-lock.yaml": "lockfileVersion: '9.0'\n"})
        contracts = [REQUIRED_CONTRACT] if include_contract else []
        plugin = root / "plugin"
        plugin_commit = self._repository(plugin, {
            "presets/modus/compatibility.json": json.dumps({
                "schema": "dsh-modus-compatibility-v1",
                "dsh": {"tested_commit": dsh_commit},
                "contracts": contracts,
            }),
            "scripts/check_dsh_compat.py": "raise SystemExit(0)\n",
        })
        return temporary, dsh, plugin, plugin_commit

    @staticmethod
    def _successful_runner(command, cwd):
        return subprocess.CompletedProcess(command, 0, "pass\n", "")

    def test_pass_requires_pinned_clean_repositories_and_both_gates(self):
        temporary, dsh, plugin, plugin_commit = self._fixture()
        self.addCleanup(temporary.cleanup)
        result = run_dsh_preflight(
            dsh_root=dsh,
            plugin_root=plugin,
            expected_plugin_commit=plugin_commit,
            runner=self._successful_runner,
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["model_requests"], 0)
        self.assertEqual(
            [gate["name"] for gate in result["gates"]],
            ["frozen-offline-lockfile", "real-dsh-compatibility"],
        )

    def test_old_plugin_without_auxiliary_tool_contract_fails_before_gates(self):
        temporary, dsh, plugin, plugin_commit = self._fixture(include_contract=False)
        self.addCleanup(temporary.cleanup)
        calls = []

        def runner(command, cwd):
            calls.append((command, cwd))
            return self._successful_runner(command, cwd)

        result = run_dsh_preflight(
            dsh_root=dsh,
            plugin_root=plugin,
            expected_plugin_commit=plugin_commit,
            runner=runner,
        )
        self.assertEqual(result["status"], "fail")
        self.assertIn("lacks required contract", result["error"])
        self.assertEqual(calls, [])
        self.assertEqual(result["model_requests"], 0)

    def test_dirty_plugin_fails_before_dependency_or_runtime_commands(self):
        temporary, dsh, plugin, plugin_commit = self._fixture()
        self.addCleanup(temporary.cleanup)
        (plugin / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        calls = []

        def runner(command, cwd):
            calls.append((command, cwd))
            return self._successful_runner(command, cwd)

        result = run_dsh_preflight(
            dsh_root=dsh,
            plugin_root=plugin,
            expected_plugin_commit=plugin_commit,
            runner=runner,
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["error"], "plugin worktree is dirty")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()

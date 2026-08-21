from pathlib import Path
import subprocess
import tempfile
import unittest

from acrouter_repro.task_runtime_preflight import (
    run_task_runtime_preflight,
    worker_environment,
)


class TaskRuntimePreflightTest(unittest.TestCase):
    def test_worker_environment_isolates_home_and_disables_dependency_downloads(self):
        value = worker_environment(
            isolated_home=Path("/run/home"),
            mamba_root=Path("/runtime/mamba"),
            source={"PATH": "/bin", "UNRELATED_SECRET": "not-forwarded"},
        )
        self.assertEqual(value["HOME"], "/run/home")
        self.assertEqual(value["MAMBA_ROOT_PREFIX"], "/runtime/mamba")
        self.assertEqual(value["PIP_NO_INDEX"], "1")
        self.assertEqual(value["PIP_REQUIRE_VIRTUALENV"], "1")
        self.assertNotIn("UNRELATED_SECRET", value)

    def test_existing_environment_and_successful_command_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            home = root / "home"
            mamba = root / "mamba"
            workspace.mkdir()
            python = mamba / "envs" / "fixture" / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.write_text("fixture\n", encoding="utf-8")
            calls = []

            def runner(command, cwd, environment):
                calls.append((command, cwd, environment))
                return subprocess.CompletedProcess(command, 0, "pass\n", "")

            result = run_task_runtime_preflight(
                workspace=workspace,
                isolated_home=home,
                mamba_root=mamba,
                environment_name="fixture",
                python_arguments=["tests/run.py", "focused"],
                runner=runner,
            )
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["model_requests"], 0)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][1], workspace.resolve())
            self.assertEqual(calls[0][2]["HOME"], str(home.resolve()))
            self.assertEqual(calls[0][2]["MAMBA_ROOT_PREFIX"], str(mamba.resolve()))

    def test_missing_environment_fails_before_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            calls = []

            def runner(command, cwd, environment):
                calls.append((command, cwd, environment))
                return subprocess.CompletedProcess(command, 0, "", "")

            result = run_task_runtime_preflight(
                workspace=workspace,
                isolated_home=root / "home",
                mamba_root=root / "mamba",
                environment_name="missing",
                python_arguments=["tests/run.py"],
                runner=runner,
            )
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["error"], "declared micromamba environment is missing")
            self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()

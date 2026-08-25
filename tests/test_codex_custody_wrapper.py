from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from acrouter_repro.codex_custody_wrapper import build_profile
from acrouter_repro.codex_custody_wrapper_v6 import build_profile as build_profile_v6


class CodexCustodyWrapperTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("sandbox-exec"), "macOS sandbox-exec required")
    def test_current_cell_is_readable_but_sibling_and_owner_repo_are_denied(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as owner:
            run_root = Path(temporary).resolve()
            cell_root = run_root / "cells/current"
            workspace = cell_root / "workspace"
            sibling = run_root / "cells/other/workspace"
            workspace.mkdir(parents=True)
            sibling.mkdir(parents=True)
            allowed = workspace / "allowed.txt"; allowed.write_text("allowed")
            sibling_secret = sibling / "sibling.txt"; sibling_secret.write_text("sibling")
            owner_secret = Path(owner).resolve() / "owner.txt"; owner_secret.write_text("owner")
            profile = build_profile(workspace, [Path(owner)])
            command = [
                "sandbox-exec", "-p", profile, "/bin/zsh", "-lc",
                f"cat {allowed}; cat {sibling_secret}; cat {owner_secret}",
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("allowed", result.stdout)
            self.assertNotIn("sibling", result.stdout)
            self.assertNotIn("owner", result.stdout)

    @unittest.skipUnless(shutil.which("sandbox-exec"), "macOS sandbox-exec required")
    def test_v6_denies_unrelated_historical_tmp_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_root = Path(temporary).resolve()
            workspace = run_root / "cells/current/workspace"
            workspace.mkdir(parents=True)
            allowed = workspace / "allowed.txt"; allowed.write_text("allowed")
            historical = Path("/private/tmp/modus-p2r-unit-historical")
            historical.mkdir(exist_ok=True)
            secret = historical / "secret.txt"; secret.write_text("historical-secret")
            try:
                profile = build_profile_v6(workspace, [])
                result = subprocess.run(
                    ["sandbox-exec", "-p", profile, "/bin/zsh", "-lc", f"cat {allowed}; cat {secret}"],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("allowed", result.stdout)
                self.assertNotIn("historical-secret", result.stdout)
            finally:
                secret.unlink(missing_ok=True)
                historical.rmdir()


if __name__ == "__main__":
    unittest.main()

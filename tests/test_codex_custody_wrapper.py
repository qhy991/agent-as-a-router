from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from acrouter_repro.codex_custody_wrapper import build_profile


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


if __name__ == "__main__":
    unittest.main()

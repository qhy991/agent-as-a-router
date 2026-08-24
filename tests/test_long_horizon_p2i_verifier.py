from pathlib import Path
import sys
import tempfile
import unittest

from scripts.verify_modus_long_horizon_p2i_stage import _mechanism


class LongHorizonP2iVerifierTest(unittest.TestCase):
    def test_semantic_mechanism_accepts_an_alternative_untagged_representation(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            package = workspace / "perf_linked_keyedmax"
            package.mkdir()
            (package / "__init__.py").write_text("")
            (package / "shared.py").write_text(
                "def build_index(rows):\n"
                "    maxima = {}\n"
                "    for key, value in rows:\n"
                "        if key not in maxima or value > maxima[key]:\n"
                "            maxima[key] = value\n"
                "    return {'maxima': maxima}\n"
            )
            (package / "observer.py").write_text(
                "from .shared import build_index\n\n"
                "def prepare_input(data):\n"
                "    return build_index(data)\n"
            )
            (package / "target.py").write_text(
                "def answer(prepared, queries):\n"
                "    maxima = prepared['maxima']\n"
                "    return [maxima.get(query) for query in queries]\n"
            )
            result = _mechanism(workspace, sys.executable)
            self.assertTrue(result["success"], result)


if __name__ == "__main__":
    unittest.main()

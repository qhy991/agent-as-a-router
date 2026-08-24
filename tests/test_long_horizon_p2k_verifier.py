from pathlib import Path
import sys
import tempfile
import unittest

from scripts.verify_modus_long_horizon_p2k_stage import _mechanism


class LongHorizonP2kVerifierTest(unittest.TestCase):
    def test_semantic_mechanism_accepts_an_alternative_untagged_representation(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            package = workspace / "perf_linked_distinctsum"
            package.mkdir()
            (package / "__init__.py").write_text("")
            (package / "shared.py").write_text(
                "def build_index(rows):\n"
                "    values = {}\n"
                "    for key, value in rows:\n"
                "        values.setdefault(key, set()).add(value)\n"
                "    return {'totals': {key: sum(items) for key, items in values.items()}}\n"
            )
            (package / "observer.py").write_text(
                "from .shared import build_index\n\n"
                "def prepare_input(data):\n"
                "    return build_index(data)\n"
            )
            (package / "target.py").write_text(
                "def answer(prepared, queries):\n"
                "    totals = prepared['totals']\n"
                "    return [totals.get(query, 0) for query in queries]\n"
            )
            result = _mechanism(workspace, sys.executable)
            self.assertTrue(result["success"], result)


if __name__ == "__main__":
    unittest.main()

import unittest
from perf_linked_keyedmax.api import execute


class PublicTest(unittest.TestCase):
    def test_keyed_max(self):
        rows = (("a", -2), ("a", 5), ("b", -7), ("a", 3))
        self.assertEqual(execute(rows, (("a", "b", "missing"),)), [[5, -7, None]])

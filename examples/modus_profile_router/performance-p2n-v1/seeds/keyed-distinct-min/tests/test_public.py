import unittest
from perf_keyed_distinct_min_p2n.api import execute


class PublicTest(unittest.TestCase):
    def test_minimum(self):
        rows = (("a", 4), ("a", -2), ("a", -2), ("b", 7))
        self.assertEqual(execute(rows, (("a", "b", "x"),)), [[-2, 7, None]])

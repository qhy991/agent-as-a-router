import unittest
from perf_keyed_distinct_quartic_sum_p2q.api import execute


class PublicTest(unittest.TestCase):
    def test_quartic_sum(self):
        rows = (("a", -2), ("a", -2), ("a", 3), ("b", 4))
        self.assertEqual(execute(rows, (("a", "b", "x"),)), [[97, 256, 0]])

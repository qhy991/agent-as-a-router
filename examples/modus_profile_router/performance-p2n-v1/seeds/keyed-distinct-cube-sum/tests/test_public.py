import unittest
from perf_keyed_distinct_cube_sum_p2n.api import execute


class PublicTest(unittest.TestCase):
    def test_cube_sum(self):
        rows = (("a", -2), ("a", -2), ("a", 3), ("b", 4))
        self.assertEqual(execute(rows, (("a", "b", "x"),)), [[19, 64, 0]])

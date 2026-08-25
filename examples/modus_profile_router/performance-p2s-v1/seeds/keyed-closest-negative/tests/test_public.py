import unittest
from perf_keyed_closest_negative_p2s.api import execute


class PublicTest(unittest.TestCase):
    def test_closest_negative(self):
        rows = (("a", -8), ("a", -2), ("a", 3), ("b", 7))
        self.assertEqual(execute(rows, (("a", "b", "x"),)), [[-2, None, None]])

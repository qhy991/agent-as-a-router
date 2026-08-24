import unittest
from perf_linked_distinctsum.api import execute


class PublicTest(unittest.TestCase):
    def test_keyed_distinct_sum(self):
        rows = (("a", -2), ("a", -2), ("a", 5), ("b", -7), ("a", 3))
        self.assertEqual(execute(rows, (("a", "b", "missing"),)), [[6, -7, 0]])

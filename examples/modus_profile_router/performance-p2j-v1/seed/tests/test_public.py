import unittest
from perf_groupdistinct_p2j.api import execute


class PublicTest(unittest.TestCase):
    def test_group_distinct(self):
        rows = (("a", 1), ("a", 1), ("a", 2), ("b", 2))
        self.assertEqual(execute(rows, (("a", "b", "missing"),)), [[2, 1, 0]])

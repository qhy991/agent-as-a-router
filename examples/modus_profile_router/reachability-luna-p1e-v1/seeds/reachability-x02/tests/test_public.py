import unittest
from perf_reachability_x02.api import execute


class PublicTest(unittest.TestCase):
    def test_reachability(self):
        edges = ((0, 1), (1, 2), (3, 4))
        self.assertEqual(execute(edges, (((0, 2), (2, 0), (3, 4), (9, 9)),)), [[True, False, True, True]])

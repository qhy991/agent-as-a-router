import unittest
from perf_linked_outdegree.api import execute


class PublicTest(unittest.TestCase):
    def test_distinct_out_degree(self):
        edges = ((0, 1), (0, 1), (0, 2), (2, 0))
        self.assertEqual(execute(edges, ((0, 1, 2, 9),)), [[2, 0, 1, 0]])

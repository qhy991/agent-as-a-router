import unittest
from perf_linked_connectivity.api import execute


class PublicTest(unittest.TestCase):
    def test_connectivity(self):
        edges = ((0, 1), (1, 2), (4, 5))
        self.assertEqual(
            execute(edges, (((0, 2), (2, 0), (0, 5), (9, 9)),)),
            [[True, True, False, True]],
        )

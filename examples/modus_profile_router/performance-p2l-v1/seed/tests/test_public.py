import unittest
from perf_energy_p2l.api import execute


class PublicTest(unittest.TestCase):
    def test_keyed_distinct_energy(self):
        rows = (("a", -2), ("a", -2), ("a", 5), ("b", -7), ("a", 3))
        self.assertEqual(execute(rows, (("a", "b", "missing"),)), [[38, 49, 0]])

import unittest
from perf_linked_rangesum.api import execute


class PublicTest(unittest.TestCase):
    def test_ranges(self):
        self.assertEqual(execute((1, 2, 3, 4), (((0, 2), (1, 4), (-3, 20), (3, 1)),)), [[3, 9, 10, 0]])

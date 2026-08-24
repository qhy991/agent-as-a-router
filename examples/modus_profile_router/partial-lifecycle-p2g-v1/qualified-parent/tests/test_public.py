import unittest
from perf_linked_frequency.api import execute


class PublicTest(unittest.TestCase):
    def test_frequency(self):
        self.assertEqual(execute(("a", "b", "a"), (("a", "b", "c"),)), [[2, 1, 0]])

import unittest
from perf_linked_membership.api import execute


class PublicTest(unittest.TestCase):
    def test_membership(self):
        self.assertEqual(execute((3, 1, 3), ((1, 2), (3, 4))), [[True, False], [True, False]])

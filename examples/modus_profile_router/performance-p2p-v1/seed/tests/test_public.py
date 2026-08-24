import unittest
from perf_direct_bitmix_p2p.api import execute
class PublicTest(unittest.TestCase):
    def test_bitmix(self):
        self.assertEqual(execute((3, 5, -2, 17), ((0, 1, 7),)), [[13, 8, 1]])

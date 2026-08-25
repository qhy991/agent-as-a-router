import unittest
from perf_rotate_mix32_p2s.api import execute


class PublicTest(unittest.TestCase):
    def test_rotate_mix(self):
        self.assertEqual(execute((1, 3, 5, -2, 17), ((0, 1, 7),)), [[13, 3, 12]])

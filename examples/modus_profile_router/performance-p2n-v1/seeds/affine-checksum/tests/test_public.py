import unittest
from perf_affine_checksum_p2n.api import execute


class PublicTest(unittest.TestCase):
    def test_affine(self):
        self.assertEqual(execute((3, -2, 11), ((0, 1, 5),)), [[9, 1, 2]])

import unittest
from modus_invariant_crc_transform.api import execute


class PublicTest(unittest.TestCase):
    def test_crc(self):
        self.assertEqual(execute((7, 0, 0), (((1, 2, 3), (255,)),)), [[72, 243]])

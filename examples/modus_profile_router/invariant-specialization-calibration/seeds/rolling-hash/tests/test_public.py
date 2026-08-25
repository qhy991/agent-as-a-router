import unittest
from modus_invariant_rolling_hash.api import execute


class PublicTest(unittest.TestCase):
    def test_hash(self):
        self.assertEqual(execute((31, 7, 1009), (((1, 2, 3), (7, 7)),)), [[880, 0]])

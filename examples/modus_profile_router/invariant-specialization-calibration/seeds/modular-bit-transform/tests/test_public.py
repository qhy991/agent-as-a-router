import unittest
from modus_invariant_modular_bit_transform.api import execute


class PublicTest(unittest.TestCase):
    def test_transform(self):
        self.assertEqual(execute((1, 3, 5, -2, 17), ((0, 1, 7),)), [[13, 3, 12]])

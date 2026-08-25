import unittest
from modus_invariant_polynomial_transform.api import execute


class PublicTest(unittest.TestCase):
    def test_polynomial(self):
        self.assertEqual(execute(((2, -3, 5), 17), ((0, 1, 3),)), [[5, 4, 14]])

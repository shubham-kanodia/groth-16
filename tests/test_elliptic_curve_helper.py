from unittest import TestCase
from helpers.elliptic_curve_helper import EllipticCurveHelper

from fields.field import FQ


class TestEllipticCurveHelper(TestCase):
    ech = EllipticCurveHelper()

    def test_addition_and_multiplication(self):
        self.assertTrue(
            self.ech.eq(
                self.ech.add(
                    self.ech.multiply(self.ech.g1_encrypt(FQ(-1).val), 5),
                    self.ech.multiply(self.ech.g1_encrypt(FQ(2).val), 6)
                ),
                self.ech.g1_encrypt(FQ(-1).val * 5 + FQ(2).val * 6)
            )
        )

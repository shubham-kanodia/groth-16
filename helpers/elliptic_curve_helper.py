import random

from py_ecc import optimized_bls12_381 as curve
from fields.field import FQ


class EllipticCurveHelper:
    G1 = curve.optimized_curve.G1
    G2 = curve.optimized_curve.G2

    RANDOM_LOWER_LIMIT = 200
    RANDOM_UPPER_LIMIT = 500

    NUMBER_OF_PARTICIPANTS = 100

    N1 = 4096
    N2 = 16

    def generate_random_number(self):
        return FQ(random.randint(self.RANDOM_LOWER_LIMIT, self.RANDOM_UPPER_LIMIT)).val

    def g1_encrypt(self, val):
        return curve.multiply(self.G1, val)

    def g2_encrypt(self, val):
        return curve.multiply(self.G2, val)

    @staticmethod
    def multiply(point, val):
        return curve.multiply(point, val)

    @staticmethod
    def add(point1, point2):
        return curve.add(point1, point2)

    def add_points(self, points):
        result = points[0]

        for point in points[1:]:
            result = self.add(result, point)

        return result

    @staticmethod
    def eq(point1, point2):
        return curve.eq(point1, point2)

    def evaluate_polynomial_at_hiding(self, poly, powers_of_tau):
        result = self.multiply(
            powers_of_tau[0],
            poly.coeffs[0].val
        )

        for c, power_of_tau in zip(poly.coeffs[1:], powers_of_tau[1:]):
            result = self.add(
                self.multiply(power_of_tau, c.val),
                result
            )
        return result

    @staticmethod
    def pairing(point_in_g1, point_in_g2):
        return curve.pairing(point_in_g2, point_in_g1)

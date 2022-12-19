import random

from py_ecc import optimized_bls12_381 as curve


class SetupHelper:
    G1 = curve.optimized_curve.G1
    G2 = curve.optimized_curve.G2

    RANDOM_LOWER_LIMIT = 200
    RANDOM_UPPER_LIMIT = 500

    NUMBER_OF_PARTICIPANTS = 100

    N1 = 4096
    N2 = 16

    def generate_random_number(self):
        return random.randint(self.RANDOM_LOWER_LIMIT, self.RANDOM_UPPER_LIMIT)

    def g1_encrypt(self, val):
        return curve.multiply(self.G1, val)

    def g2_encrypt(self, val):
        return curve.multiply(self.G2, val)

    @staticmethod
    def multiply(point, val):
        return curve.multiply(point, val)
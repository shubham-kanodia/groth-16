from typing import List


class Polynomial:
    def __init__(self, coeffs: List[float]):
        self.coeffs = coeffs
        self.degree = len(coeffs) - 1

    def __mul__(self, other):
        final_coeffs = [0 for _ in range(other.degree + self.degree + 1)]

        for idx_a in range(0, len(self.coeffs)):
            for idx_b in range(0, len(other.coeffs)):
                final_coeffs[idx_a + idx_b] += self.coeffs[idx_a] * other.coeffs[idx_b]

        return Polynomial(final_coeffs)

    def __add__(self, other):
        coeffs_a = self.coeffs if len(self.coeffs) > len(other.coeffs) else other.coeffs
        coeffs_b = self.coeffs if len(self.coeffs) <= len(other.coeffs) else other.coeffs

        for idx in range(len(coeffs_b)):
            coeffs_a[idx] += coeffs_b[idx]

        return Polynomial(coeffs_a)

    def __sub__(self, other):
        coeffs_a = self.coeffs if len(self.coeffs) > len(other.coeffs) else other.coeffs
        coeffs_b = self.coeffs if len(self.coeffs) <= len(other.coeffs) else other.coeffs

        coeffs_b = coeffs_b + [0 for _ in range(len(coeffs_a) - len(coeffs_b))]

        if coeffs_a != self.coeffs:
            coeffs_a, coeffs_b = coeffs_b, coeffs_a

        for idx in range(len(coeffs_a)):
            coeffs_a[idx] -= coeffs_b[idx]

        return Polynomial(coeffs_a)

    @staticmethod
    def from_points(points):
        lps = []

        for point_a in points:
            poly = Polynomial([1])
            for point_b in points:
                if point_a != point_b:
                    poly = poly * Polynomial([-1 * point_b[0], 1])
                    poly = poly * Polynomial([1.0 / (point_a[0] - point_b[0])])

            poly = poly * Polynomial([point_a[1]])
            lps.append(poly)

        final_polynomial = Polynomial([0])
        for poly in lps:
            final_polynomial += poly

        return final_polynomial


# poly_a = Polynomial([1, 3, 0, 1])
# poly_b = Polynomial([3, 0, 3])
# A1(1) = 0, A1(2) = 0, A1(3) = 0, A1(4) = 5

# points = [(1, 0), (2, 0), (3, 0), (4, 5)]
# print(Polynomial.from_points(points).coeffs)

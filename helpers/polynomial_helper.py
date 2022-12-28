from typing import List, Union
from fields.field import FQ


class Polynomial:
    def __init__(self, coeffs: List[Union[float, FQ]]):
        self.coeffs = [FQ(_) if not isinstance(_, FQ) else _ for _ in coeffs]
        self.degree = len(coeffs) - 1

    def __mul__(self, other):
        final_coeffs = [FQ(0) for _ in range(other.degree + self.degree + 1)]

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

        coeffs_b = coeffs_b + [FQ(0) for _ in range(len(coeffs_a) - len(coeffs_b))]

        if coeffs_a != self.coeffs:
            coeffs_a, coeffs_b = coeffs_b, coeffs_a

        for idx in range(len(coeffs_a)):
            coeffs_a[idx] -= coeffs_b[idx]

        return Polynomial(coeffs_a)

    def __truediv__(self, other):
        result_coeffs = [FQ(0) for _ in range(self.degree - other.degree + 1)]
        remainder = self

        for idx in range(self.degree - other.degree + 1):
            self_power_of_x = len(remainder.coeffs) - idx - 1
            other_power_of_x = len(other.coeffs) - 1

            self_coeff = remainder.coeffs[self_power_of_x]
            other_coeff = other.coeffs[other_power_of_x]

            max_degree = self_power_of_x - other_power_of_x

            mult_poly = [FQ(0) if idx < max_degree else (self_coeff / other_coeff) for idx in range(max_degree + 1)]
            result_coeffs[max_degree] = (self_coeff / other_coeff)

            remainder = remainder - (other * Polynomial(mult_poly))

        if not all([_.val for _ in remainder.coeffs]):
            return Polynomial(result_coeffs)
        else:
            raise Exception("Polynomials not divisible")

    def __repr__(self):
        return f"{', '.join([str(_.val) for _ in self.coeffs])}"

    @staticmethod
    def from_points(points):
        lps = []

        for point_a in points:
            poly = Polynomial([1])
            for point_b in points:
                if point_a != point_b:
                    poly = poly * Polynomial([FQ(-1) * point_b[0], 1])
                    poly = poly * Polynomial([FQ(1) / (point_a[0] - point_b[0])])

            poly = poly * Polynomial([point_a[1]])
            lps.append(poly)

        final_polynomial = Polynomial([0])
        for poly in lps:
            final_polynomial += poly

        return final_polynomial

    def evaluate(self, x):
        result = FQ(0)
        for idx, c in enumerate(self.coeffs):
            result += c * FQ(pow(x, idx, FQ.p))
        return result

    @staticmethod
    def sum(polynomials):
        result = Polynomial([FQ(0)])

        for poly in polynomials:
            result = result + poly

        return result

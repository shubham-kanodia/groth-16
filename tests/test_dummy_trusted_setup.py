from unittest import TestCase
from helpers.dummy_trusted_setup import DummyTrustedSetup
from helpers.elliptic_curve_helper import EllipticCurveHelper
from helpers.polynomial_helper import Polynomial

from fields.field import FQ


class TestDummyTrustedSetup(TestCase):
    ech = EllipticCurveHelper()
    trusted_setup = DummyTrustedSetup(ech)

    trusted_setup.execute_phase_1()
    test_polynomial = Polynomial([FQ(6), FQ(-5), FQ(1)])

    def test_compute_powers_of_tau(self):
        dummy_tau = FQ(-10).val
        generator = self.ech.G1
        elements = 20

        powers_of_tau = self.trusted_setup._compute_powers_of_tau(generator, dummy_tau, elements)
        for idx, power_of_tau in enumerate(powers_of_tau):
            self.assertTrue(self.ech.eq(
                self.ech.g1_encrypt(pow(dummy_tau, idx)),
                power_of_tau
            ))

    def test_powers_of_tau_evaluation(self):
        # Test with powers of tau in G1
        result = self.test_polynomial.evaluate(self.trusted_setup.tau)
        result_in_g1 = self.ech.multiply(self.ech.G1, result)

        evaluation_using_powers_of_tau = self.ech.evaluate_polynomial_at_hiding(
            self.test_polynomial,
            self.trusted_setup.powers_of_tau_in_g1
        )
        self.assertTrue(self.ech.eq(result_in_g1, evaluation_using_powers_of_tau))

        # Test with powers of tau in G2
        result_in_g2 = self.ech.multiply(self.ech.G2, result)

        evaluation_using_powers_of_tau = self.ech.evaluate_polynomial_at_hiding(
            self.test_polynomial,
            self.trusted_setup.powers_of_tau_in_g2
        )

        self.assertTrue(self.ech.eq(result_in_g2, evaluation_using_powers_of_tau))

    def test_alpha_evaluation(self):
        result = self.trusted_setup.alpha * self.test_polynomial.evaluate(self.trusted_setup.tau)
        result_in_g1 = self.ech.multiply(self.ech.G1, result)

        evaluation_using_powers_of_tau_with_alpha = self.ech.evaluate_polynomial_at_hiding(
            self.test_polynomial,
            self.trusted_setup.powers_of_tau_in_g1_product_alpha
        )

        self.assertTrue(self.ech.eq(
            result_in_g1, evaluation_using_powers_of_tau_with_alpha)
        )

    def test_beta_evaluation(self):
        result = self.trusted_setup.beta * self.test_polynomial.evaluate(self.trusted_setup.tau)
        result_in_g1 = self.ech.multiply(self.ech.G1, result)

        evaluation_using_powers_of_tau_with_beta = self.ech.evaluate_polynomial_at_hiding(
            self.test_polynomial,
            self.trusted_setup.powers_of_tau_in_g1_product_beta
        )

        self.assertTrue(self.ech.eq(
            result_in_g1, evaluation_using_powers_of_tau_with_beta)
        )

    def test_compute_li(self):
        dummy_qap_a = [Polynomial([FQ(1), FQ(2), FQ(6)])]
        dummy_qap_b = [Polynomial([FQ(2), FQ(0), FQ(3)])]
        dummy_qap_c = [Polynomial([FQ(1), FQ(4), FQ(7)])]

        for idx in range(len(dummy_qap_a)):
            result_in_g1 = self.trusted_setup.compute_li(idx, dummy_qap_a, dummy_qap_b, dummy_qap_c)

            evaluation = self.trusted_setup.beta * dummy_qap_a[idx].evaluate(self.trusted_setup.tau) + \
                         self.trusted_setup.alpha * dummy_qap_b[idx].evaluate(self.trusted_setup.tau) + \
                         dummy_qap_c[idx].evaluate(self.trusted_setup.tau)

            evaluation_in_g1 = self.ech.multiply(self.ech.G1, evaluation)

            self.assertTrue(self.ech.eq(result_in_g1, evaluation_in_g1))

    def test_zx_function(self):
        zx = self.trusted_setup.calculate_zx(4)
        expected_coeffs = [FQ(24), FQ(-50), FQ(35), FQ(-10), FQ(1)]

        for actual_coeff, expected_coeff in zip(zx.coeffs, expected_coeffs):
            self.assertEqual(actual_coeff.val, expected_coeff.val)
